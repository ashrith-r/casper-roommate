"""Measured matching quality; no fixed benchmark figures."""
import numpy as np

def compute_variance(scores):
    return float(np.var(scores)) if len(scores) else 0.0

def metrics(pairs, graph, population):
    scores = [float(graph['score'][a,b]) for a,b in pairs]
    cs = [float(graph['cs'][a,b]) for a,b in pairs]
    cf = [float(graph['cf'][a,b]) for a,b in pairs]
    return {'pairs':len(pairs),'unmatched':population-2*len(pairs),
            'coverage':2*len(pairs)/population if population else 0,
            'total':float(sum(scores)), 'mean':float(np.mean(scores)) if scores else 0,
            'minimum':float(min(scores)) if scores else 0, 'variance':compute_variance(scores),
            'compatibility':float(np.mean(cs)) if cs else 0,'conflict':float(np.mean(cf)) if cf else 0}
