"""Five measured methods on the same feasible graph."""
from time import perf_counter

from src.baselines.baselines import BaselineRunner
from src.graph.graph_builder import build_score_dict
from src.graph.optimizer import improve_matching_tracked

LABELS = {'random': 'Random feasible', 'greedy': 'Score greedy', 'blossom': 'Blossom',
          'v1': 'Blossom + one swap pattern', 'v2': 'Blossom + both patterns'}
COSTS = {'random': 'O(E)', 'greedy': 'O(E log E)', 'blossom': 'O(N³)',
         'v1': 'O(N³ + I P²)', 'v2': 'O(N³ + I P²)'}


def percentage(value, base):
    return 100 * (value - base) / abs(base) if base else None


def coverage_paths(greedy, exact):
    """Extract disjoint augmenting paths in the difference of two matchings."""
    gmate = {a: b for edge in greedy for a, b in (edge, edge[::-1])}
    emate = {a: b for edge in exact for a, b in (edge, edge[::-1])}
    paths = []
    for start in sorted(emate.keys() - gmate.keys()):
        path = [start]
        while path[-1] in emate:
            partner = emate[path[-1]]
            path.append(partner)
            if partner not in gmate:
                # Both ends are free in greedy. Save just one orientation.
                if start < partner:
                    paths.append(path)
                break
            path.append(gmate[partner])
    return sorted(paths, key=lambda path: (len(path), path))


def run_full_benchmark(graph, *, seed=42, trials=200):
    if trials < 1:
        raise ValueError('Use at least one random trial.')
    scores = build_score_dict(graph['edges'])
    runner = BaselineRunner(graph, scores)
    random_row, random_pairs = runner.random_assignment(trials, seed)
    rows = {'random': random_row}
    pairs = {'random': random_pairs}
    traces = {}
    for key in ('greedy', 'blossom', 'v1', 'v2'):
        start = perf_counter()
        if key == 'greedy':
            pairs[key] = runner.greedy_assignment()
        elif key == 'blossom':
            pairs[key] = runner.blossom_only()
        else:
            pairs[key], history, log = runner.refined(both=key == 'v2')
            traces[key] = dict(history=history, log=log)
        elapsed = perf_counter() - start
        rows[key] = dict(runner.measure(pairs[key]), seconds=elapsed)

    # A greedy start exposes real local moves when the exact start is stationary.
    _, history, log = improve_matching_tracked(pairs['greedy'], scores)
    traces['greedy'] = dict(history=history, log=log)
    for key, row in rows.items():
        row['v2_gain_pct'] = percentage(rows['v2']['total'], row['total'])
    return dict(seed=seed, trials=trials, nodes=runner.n, eligible=len(runner.edges),
                methods=rows, pairs=pairs, traces=traces,
                coverage_paths=coverage_paths(pairs['greedy'], pairs['blossom']))


def print_benchmark_table(report):
    print(f"{'Method':30} {'Pairs':>7} {'Total':>9} {'Neg.':>7} {'ms/run':>10} {'v2 gain':>9}")
    for key, row in report['methods'].items():
        gain = row['v2_gain_pct']
        change = 'n/a' if gain is None else f'{gain:+.2f}%'
        print(f"{LABELS[key]:30} {row['pairs']:7.2f} {row['total']:9.3f} "
              f"{row['negative_pairs']:7.2f} {1000 * row['seconds']:10.3f} {change:>9}")
    paths = report['coverage_paths']
    if paths:
        print(f'{len(paths)} disjoint augmenting paths explain the coverage gap.')
        print('Shortest path (one-based rows):', ' -> '.join(str(i+1) for i in paths[0]))
