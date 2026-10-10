# CASPER algorithm

## Features and scoring

All eleven supplied numeric responses are validated on the 0–10 scale, then divided by ten: social personality, English proficiency, cleanliness, sleep time, noise tolerance, irritability, visitor frequency, music habit, non-vegetarian food frequency, snoring frequency and snoring sensitivity. Original questionnaire scale anchors are not reconstructed or invented.

Six interest indicators follow the original implementation: coding, music, sports, gaming, studies and social. Satisfaction is descriptive only and never a matching feature.

For normalized vectors `x`, and interest sets `H`:

```text
numeric_similarity = 1 − mean(|x_i − x_j|)
Jaccard = |H_i ∩ H_j| / (|H_i ∪ H_j| + 10⁻⁶)
CS = 0.6 × numeric_similarity + 0.4 × Jaccard

CF = 0.15 × (|snore_i − sensitivity_j| + |sensitivity_i − snore_j|)
   + 0.15 × (|noise_i − visitors_j| + |visitors_i − noise_j|)
   + 0.20 × |sleep_i − sleep_j|
   + 0.10 × (irritability_i + irritability_j)

S = CS − λ × CF²
```

`CS` preserves the ZIP's numeric and interest model. `CF` is the mean of its forward and reverse conflicts; this is the approved correction for row-order dependence. The ZIP's interpretations of these survey values are retained. This is a preference model rather than a validated prediction of interpersonal conflict.

## Eligibility and selection

1. Construct all pair scores in Python using NumPy.
2. Retain only pairs in the same supplied hostel cohort and with `CF ≤ threshold`. Default threshold: 0.4; default λ: 0.5.
3. Send eligible numeric edges to C++ through standard input. No names or emails enter the engine.
4. Push edges into a maximum priority queue. Prefer larger scores; tie-break by participant row indices for reproducibility.
5. Select an edge only when both endpoints are unused. Negative edges are not separately pruned: eligibility follows the configured conflict and cohort rules.
6. Refine pairs for at most 12 sweeps by default, with an allowed setting range of 0–50.
7. Return all unpaired participants explicitly. A restrictive threshold, odd cohort size or greedy selection can leave participants unmatched.

Determinism applies to a fixed input order. Symmetric pair scores do not imply that all tied matchings are invariant under a permutation of the input rows.

## Fairness refinement

For pairs `(a,b)` and `(c,d)`, check both `(a,c),(b,d)` and `(a,d),(b,c)`. Both proposed edges must be eligible. With fairness enabled, acceptance requires:

- Nondecreasing total adjusted score.
- Nondecreasing smaller score among the two affected pairs.
- Nonincreasing variance over the pool being refined.
- At least one strict improvement in these criteria.

Comparisons use tolerance `10⁻¹⁰`. At fixed pair count this protects the pool's weakest pair and variance while preserving its total. It is a constrained local improvement rule, not a global fairness optimizer. With fairness disabled, a swap must increase total score. The engine reports whether it observed convergence before the sweep limit.

Preserved online pairs are removed from the candidate pool and reattached unchanged after refinement. Fairness guarantees then apply to the unlocked pool, not the combined variance of locked and unlocked scores. All preserved pairs are revalidated against current constraints. The sidebar's Run CASPER action performs a fresh full allocation; preservation is selected explicitly in the online-update form.

## Complexity

Let `n` be responses, `d` the fixed feature count, `E` eligible edges and `P` the sweep limit:

| Stage | Time |
| --- | --- |
| Feature scoring | O(n²d) |
| Heap construction and extraction | O(E log E) |
| Local refinement | O(Pn²) |
| Storage | O(n² + E) |

For fixed `d` and bounded `P`, the matching pipeline is O(n² log n) in the dense case. Pruning reduces actual edges, but does not remove the dense score matrices. An unbounded repeat-until-improved loop would not justify this bound. Optional Blossom benchmarking is additional work and is excluded from this complexity claim.

## Online and adaptive behavior

Online mode accepts actual responses without prefilled measurements. It either preserves the current allocation and matches the remaining pool or recomputes all participants. It rebuilds the score graph on each update; it is not a specialized subquadratic streaming algorithm. Session data is not durable storage.

Penalty evaluation runs nine λ values from 0 to 2. Its selection rule prioritizes paired coverage, then lower mean conflict, then higher mean compatibility, then the smaller λ. Adjusted totals from different λ values are not treated as a common quality metric. The recommendation is displayed for review rather than silently applied.

There are no linked current-roommate pairs or observed outcomes for proposed pairs in the source. Individual satisfaction alone cannot validate a supervised pair-success predictor. A trained adaptive model remains unsupported by this dataset.

## Reference comparison

NetworkX Blossom computes maximum cardinality first and maximum weight among such matchings on the identical eligible graph. It may pair more participants than CASPER. The app exposes count, coverage, total, weakest score, variance and unpenalized compatibility/conflict so tradeoffs are visible. Timings distinguish native kernel work, process overhead and Python execution; they are host-specific observations, not a universal speedup claim.
