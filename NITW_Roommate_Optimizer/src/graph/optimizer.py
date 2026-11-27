"""Replayable best-improvement search over disjoint, eligible pairs."""
from math import fsum


def improve_matching_tracked(pairs, scores, max_iterations=1000, *, both=True):
    pairs = list(map(tuple, pairs))
    history = [fsum(scores[p] for p in pairs)]
    log = []
    for _ in range(max_iterations):
        best = None
        best_gain = 1e-10
        for i, (a, b) in enumerate(pairs):
            for j in range(i + 1, len(pairs)):
                c, d = pairs[j]
                current = scores[a, b] + scores[c, d]
                choices = (((a, c), (b, d)), ((a, d), (b, c)))
                for pattern, (left, right) in enumerate(choices if both else choices[:1], 1):
                    if left not in scores or right not in scores:
                        continue
                    gain = scores[left] + scores[right] - current
                    if gain > best_gain:
                        best_gain = gain
                        best = i, j, left, right, pattern
        if best is None:
            break
        i, j, left, right, pattern = best
        before = (pairs[i], pairs[j])
        pairs[i], pairs[j] = left, right
        history.append(fsum(scores[p] for p in pairs))
        log.append(dict(iteration=len(log) + 1, pattern=pattern, slots=(i, j),
                        before=before, after=(left, right), delta=best_gain, total=history[-1]))
    return pairs, history, log
