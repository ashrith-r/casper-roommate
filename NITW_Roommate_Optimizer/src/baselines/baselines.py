"""Compare feasible allocations on one graph. Times exclude graph construction."""
import random
from statistics import fmean
from time import perf_counter

from src.graph.fallback import optimized_fallback, take_disjoint
from src.graph.matcher import max_weight_matching
from src.graph.optimizer import improve_matching_tracked
from src.optimization.fairness import metrics


class BaselineRunner:
    def __init__(self, graph, scores):
        self.graph = graph
        self.scores = scores
        self.n = len(graph['score'])
        self.edges = graph['edges']

    def measure(self, pairs):
        row = metrics(pairs, self.graph, self.n)
        row['negative_pairs'] = sum(self.scores[p] < 0 for p in pairs)
        row['maximum'] = max((self.scores[p] for p in pairs), default=0.0)
        return row

    def random_assignment(self, trials, seed):
        rng = random.Random(seed)
        samples = []
        first = None
        elapsed = 0.0
        for _ in range(trials):
            start = perf_counter()
            edges = self.edges.copy()
            rng.shuffle(edges)
            pairs = take_disjoint(edges)
            elapsed += perf_counter() - start
            if first is None:
                first = pairs
            samples.append(self.measure(pairs))
        row = {k: fmean(s[k] for s in samples) for k in samples[0]}
        return dict(row, seconds=elapsed / trials), first

    def greedy_assignment(self):
        return take_disjoint(sorted(self.edges, key=lambda e: -e[2]))

    def blossom_only(self):
        return max_weight_matching(self.edges, self.n)

    def refined(self, both):
        initial = self.blossom_only()
        used = {n for pair in initial for n in pair}
        if both:
            extra, _ = optimized_fallback(set(range(self.n)) - used, self.scores)
            initial += extra
        return improve_matching_tracked(initial, self.scores, both=both)
