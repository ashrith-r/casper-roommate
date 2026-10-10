"""Compatibility entry point for the original project layout."""
from src.data.data_cleaner import run_cleaning_pipeline, RAW_PATH, ROOT
if __name__ == '__main__':
    output = ROOT / 'data' / 'processed' / 'cleaned_data.csv'
    frame = run_cleaning_pipeline(RAW_PATH, output)
    print(f'Validated {len(frame)} survey records. Saved {output.name}.')
