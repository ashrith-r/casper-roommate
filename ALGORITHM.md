# The matching model

Each profile has five normalized values in [0,1]: cleanliness, sleep routine, social energy, snoring frequency and snoring sensitivity; plus a set of interests.

## Compatibility

For each lifestyle feature, similarity is `1 − |a − b|`.

```text
CS = 0.30 × cleanliness similarity
   + 0.30 × sleep routine similarity
   + 0.20 × social energy similarity
   + 0.20 × Jaccard(interests A, interests B)
```

Jaccard is intersection size / union size. If both interest sets are empty, compatibility is the lifestyle subtotal divided by 0.8. This treats missing interests as missing evidence. If only one set is empty, Jaccard is zero.

These weights are transparent design choices, not learned or empirically calibrated parameters.

## Conflict

```text
CF = (A.snoring × B.sensitivity + B.snoring × A.sensitivity) / 2
adjusted score = CS − λ × CF²
```

Both CF and CS lie in [0,1]. λ ranges from 0 to 2 (default 0.5). A pair is eligible only if its CF is no greater than the chosen threshold (default 0.55) and its adjusted score is positive. Threshold equality is allowed. Display scores multiply adjusted scores by 100; they are not probabilities. Accepted scores are in (0,1].

The provided C++ used absolute differences between snoring and the other person’s sensitivity. That makes two high values look conflict-free, even though frequent snoring and high sensitivity should increase modeled risk. This version intentionally changes that interpretation. It does not assert clinical or predictive validity for the replacement formula.

## Selection and refinement

1. Compute every pair and retain valid edges in a symmetric matrix.
2. Sort edges by descending adjusted score; break ties by original row indices.
3. Greedily choose edges with two unused endpoints.
4. For each two selected pairs `(a,b)` and `(c,d)`, check both `(a,c)+(b,d)` and `(a,d)+(b,c)`.
5. Only choose an alternative if both edges are eligible and the total increases by more than `1e-10`.
6. Finish when a pass makes no improvement or 10 passes have run.

The endpoint set never changes during swaps, so refinement cannot duplicate or lose students. Unmatched students are returned and included in exports. Refinement improves total score at a fixed selected pair count; it does not repair greedy cardinality failures. There are no augmenting-path or unmatched-student insertion steps in v1.

The implementation uses a sorted edge list instead of a C++ max-heap. Both produce the descending greedy edge ordering; sorting also provides explicit deterministic tie-breaking. It runs directly in the browser, without requiring a C++ backend.

## Complexity and limitations

For n people and a fixed feature set: all-pair scoring O(n²), edge sorting O(n² log n), refinement O(Pn²), with P ≤ 10; memory O(n²). Set operations also depend on the number/length of interest labels. The UI’s 200-person/2-MB limit keeps this a bounded browser demo.

The original unbounded `while(improved)` loop does not justify describing all local refinement as a single O(n²) step. A bounded pass count makes the stated complexity accurate here. Pruning reduces actual edges but does not guarantee a sparse graph. No assertion is made that this beats an exact algorithm in quality or measured speed.

“Equilibrium Regulation” is part of the supplied acronym, not an equilibrium theorem. There is no stable matching guarantee, maximum-weight proof, maximum-cardinality guarantee, or formal fairness objective. A visible lowest pair score is a diagnostic only. Nonlinear penalties model an assumed tradeoff, not validated fairness.

## Validation

`node --test tests/*.test.mjs` checks symmetric snoring risk, sparse/empty/odd cohorts, unique assignments, deterministic output, improving refinements, score monotonicity, constraints across 120 seeded cohorts, CSV quoting, original survey headings, normalized imports, malformed data and safe CSV export. This verifies software behavior, not real-world match quality.
