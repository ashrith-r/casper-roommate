"""Greedy completion on eligible edges only."""


def take_disjoint(edges):
    used = set()
    pairs = []
    for a, b, _ in edges:
        if a not in used and b not in used:
            pairs.append((a, b))
            used.update((a, b))
    return pairs


def optimized_fallback(unmatched, scores):
    nodes = sorted(unmatched)
    candidates = [(a, b, scores[a, b]) for i, a in enumerate(nodes)
                  for b in nodes[i + 1:] if (a, b) in scores]
    candidates.sort(key=lambda edge: -edge[2])
    pairs = take_disjoint(candidates)
    used = {n for pair in pairs for n in pair}
    return pairs, [n for n in nodes if n not in used]
