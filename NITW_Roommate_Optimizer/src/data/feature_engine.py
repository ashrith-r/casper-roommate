"""Original feature weights and Jaccard scoring with symmetric conflict terms."""
import numpy as np
from src.data.data_cleaner import NUMERIC, HOBBIES
NUMERIC_COLS = [c + '_norm' for c in NUMERIC]
HOBBY_COLS = ['hobby_' + h for h in HOBBIES]

def compute_cs(a, b, alpha=0.6):
    numeric = 1 - np.abs(a[NUMERIC_COLS].to_numpy(float) - b[NUMERIC_COLS].to_numpy(float)).mean()
    h1, h2 = a[HOBBY_COLS].to_numpy(int), b[HOBBY_COLS].to_numpy(int)
    intersection = np.logical_and(h1, h2).sum()
    union = np.logical_or(h1, h2).sum()
    return float(alpha * numeric + (1 - alpha) * intersection / (union + 1e-6))

def conflict_components(a, b):
    return {
        'Snoring / sensitivity': .3 * (abs(a.snore_freq_norm - b.snore_sensitivity_norm) + abs(b.snore_freq_norm - a.snore_sensitivity_norm)) / 2,
        'Noise / visitors': .3 * (abs(a.noise_tolerance_norm - b.friends_freq_norm) + abs(b.noise_tolerance_norm - a.friends_freq_norm)) / 2,
        'Sleep routine': .2 * abs(a.sleep_time_norm - b.sleep_time_norm),
        'Irritability': .2 * (a.irritability_norm + b.irritability_norm) / 2,
    }

def compute_cf(a, b):
    return float(sum(conflict_components(a, b).values()))

def score_matrices(df, alpha=0.6):
    """Vectorized O(n²k) calculations, equivalent to the scalar functions."""
    x = df[NUMERIC_COLS].to_numpy(float)
    numeric = 1 - np.abs(x[:, None, :] - x[None, :, :]).mean(axis=2)
    h = df[HOBBY_COLS].to_numpy(int)
    intersection = h @ h.T
    union = h.sum(axis=1)[:, None] + h.sum(axis=1)[None, :] - intersection
    cs = alpha * numeric + (1 - alpha) * intersection / (union + 1e-6)
    def values(key): return df[key + '_norm'].to_numpy(float)
    snore, sensitivity = values('snore_freq'), values('snore_sensitivity')
    noise, friends = values('noise_tolerance'), values('friends_freq')
    sleep, irrit = values('sleep_time'), values('irritability')
    cf = (.15 * (np.abs(snore[:,None] - sensitivity[None,:]) + np.abs(sensitivity[:,None] - snore[None,:]))
          + .15 * (np.abs(noise[:,None] - friends[None,:]) + np.abs(friends[:,None] - noise[None,:]))
          + .2 * np.abs(sleep[:,None] - sleep[None,:]) + .1 * (irrit[:,None] + irrit[None,:]))
    return cs, cf
