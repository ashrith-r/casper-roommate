"""Validate the supplied survey without inventing missing measurements."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import io
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / 'data' / 'raw' / 'raw_data.csv'
PUBLIC_PATH = ROOT / 'data' / 'processed' / 'participants.csv'
NUMERIC = ['social', 'english', 'cleanliness', 'sleep_time', 'noise_tolerance',
           'irritability', 'friends_freq', 'music_habit', 'non_veg_freq',
           'snore_freq', 'snore_sensitivity']
HOBBIES = ['coding', 'music', 'sports', 'gaming', 'studies', 'social']
COLUMN_MAP = {
    'Submission ID': 'submission_id', 'Respondent ID': 'respondent_id',
    'Submitted at': 'submitted_at', 'Full Name': 'name', 'Email': 'email',
    'Email Address': 'email', 'Gender': 'gender', 'Branch': 'branch',
    'How would you describe your social personality?': 'social',
    'English Proficiency': 'english', 'Cleaniliness': 'cleanliness',
    'Cleanliness': 'cleanliness', 'Sleep Time': 'sleep_time',
    'Noise Tolerance': 'noise_tolerance',
    'How easily do you get irritated by others?': 'irritability',
    'How often do you bring your firends to room?': 'friends_freq',
    'How do you usually listen to music?': 'music_habit',
    'How often do you eat Non-Veg?': 'non_veg_freq',
    'How often do you snore?': 'snore_freq',
    'How sensitive are you to snoring?': 'snore_sensitivity',
    '🎯 What do you do in your spare time?': 'hobbies_raw',
    'How much are you satisfied with your current roommate?': 'current_sat',
}

@dataclass
class DataAudit:
    rows: int
    numeric_features: int
    repeated_names: int
    repeated_respondents: int
    missing_emails: int
    source_sha256: str
    identified: bool

def load_data(source=RAW_PATH):
    if isinstance(source, bytes):
        payload = source
    elif hasattr(source, 'getvalue'):
        payload = source.getvalue()
    else:
        payload = Path(source).read_bytes()
    if len(payload) > 5_000_000:
        raise ValueError('CSV must be smaller than 5 MB.')
    try:
        df = pd.read_csv(io.BytesIO(payload))
    except Exception as exc:
        raise ValueError('Unable to read UTF-8 CSV.') from exc
    df.columns = df.columns.str.strip()
    df = df.rename(columns=COLUMN_MAP)
    if df.columns.duplicated().any():
        raise ValueError('Normalized column names must be unique.')
    if not 2 <= len(df) <= 1000:
        raise ValueError('Provide between 2 and 1,000 survey responses.')
    missing = [c for c in NUMERIC + ['gender'] if c not in df]
    if missing:
        raise ValueError('Missing survey columns: ' + ', '.join(missing))
    for col in NUMERIC:
        values = pd.to_numeric(df[col], errors='coerce')
        invalid = values.isna() | ~np.isfinite(values) | ~values.between(0, 10)
        if invalid.any():
            rows = ', '.join(str(i + 2) for i in np.flatnonzero(invalid)[:8])
            raise ValueError(f'{col}: expected 0–10 at CSV row(s) {rows}.')
        df[col] = values.astype(float)
        df[col + '_norm'] = df[col] / 10.0
    df['gender'] = df['gender'].astype(str).str.strip().str.capitalize()
    if not df['gender'].isin(['Male', 'Female']).all():
        raise ValueError('Gender must match the supplied hostel cohort labels: Male or Female.')
    identified = 'name' in df and 'email' in df
    if 'participant_id' not in df:
        df['participant_id'] = [f'P{i + 1:03d}' for i in range(len(df))]
    df['participant_id'] = df['participant_id'].astype(str).str.strip()
    if (~df['participant_id'].str.fullmatch(r'[A-Za-z0-9_-]{1,40}')).any() or df['participant_id'].duplicated().any():
        raise ValueError('Participant IDs must be unique letters/digits/underscores/hyphens.')
    for col in ['name', 'email', 'respondent_id', 'submission_id']:
        if col not in df:
            df[col] = ''
        df[col] = df[col].fillna('').astype(str).str.strip()
    if 'hobbies_raw' in df:
        df['hobbies_raw'] = df['hobbies_raw'].fillna('').astype(str)
        for hobby in HOBBIES:
            df['hobby_' + hobby] = df['hobbies_raw'].str.contains(hobby, case=False, regex=False).astype(int)
    elif all('hobby_' + h in df for h in HOBBIES):
        for h in HOBBIES:
            s = pd.to_numeric(df['hobby_' + h], errors='coerce')
            if not s.isin([0, 1]).all():
                raise ValueError('Hobby indicators must be 0 or 1.')
            df['hobby_' + h] = s.astype(int)
    else:
        raise ValueError('Include hobbies_raw or all six hobby indicator columns.')
    if 'current_sat' in df:
        original = df['current_sat']
        df['current_sat'] = pd.to_numeric(original, errors='coerce')
        if (original.notna() & df['current_sat'].isna()).any():
            raise ValueError('Current roommate satisfaction must be numeric or blank.')
        if not (df['current_sat'].isna() | df['current_sat'].between(1, 5)).all():
            raise ValueError('Current roommate satisfaction must be from 1 to 5.')
    else:
        df['current_sat'] = np.nan
    names = df.loc[df['name'] != '', 'name'].str.casefold()
    ids = df.loc[df['respondent_id'] != '', 'respondent_id']
    audit = DataAudit(len(df), len(NUMERIC), int(names.duplicated().sum()),
                      int(ids.duplicated().sum()), int((df['email'] == '').sum()),
                      hashlib.sha256(payload).hexdigest(), identified)
    return df.reset_index(drop=True), audit

def public_measurements(df):
    columns = ['participant_id', 'gender'] + NUMERIC + ['hobby_' + h for h in HOBBIES] + ['current_sat']
    return df[columns].copy()

def run_cleaning_pipeline(input_file=RAW_PATH, output_file=None):
    df, _ = load_data(input_file)
    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
    return df
