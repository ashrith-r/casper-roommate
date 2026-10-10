"""Construct the original same-cohort graph and apply the conflict threshold."""
from dataclasses import dataclass
import numpy as np
from src.data.feature_engine import score_matrices

@dataclass(frozen=True)
class Settings:
    lambda_: float = .5
    threshold: float = .4
    alpha: float = .6
    max_sweeps: int = 12
    fairness: bool = True

    def validate(self):
        if not np.isfinite([self.lambda_, self.threshold, self.alpha]).all():
            raise ValueError('Settings must be finite numbers.')
        if not 0 <= self.lambda_ <= 2 or not 0 <= self.threshold <= 1 or not 0 <= self.alpha <= 1:
            raise ValueError('Lambda must be 0–2; threshold and alpha must be 0–1.')
        if not isinstance(self.max_sweeps, int) or not 0 <= self.max_sweeps <= 50:
            raise ValueError('Refinement sweeps must be an integer from 0 to 50.')

def build_graph(df, settings=Settings()):
    settings.validate()
    cs, cf = score_matrices(df, settings.alpha)
    score = cs - settings.lambda_ * cf**2
    genders = df.gender.to_numpy()
    same = genders[:,None] == genders[None,:]
    allowed = same & (cf <= settings.threshold)
    np.fill_diagonal(allowed, False)
    edges = [(int(i),int(j),float(score[i,j])) for i,j in zip(*np.where(np.triu(allowed,1)))]
    possible = len(df)*(len(df)-1)//2
    group_edges = int(np.triu(same,1).sum())
    return {'cs':cs,'cf':cf,'score':score,'allowed':allowed,'edges':edges,
            'possible':possible,'cohort_exclusions':possible-group_edges,
            'conflict_exclusions':group_edges-len(edges),'eligible':len(edges)}

def build_edges(df, lambda_=.5, threshold=.4):
    return build_graph(df, Settings(lambda_=lambda_, threshold=threshold))['edges']
