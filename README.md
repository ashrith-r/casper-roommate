# CASPER | More compatible rooms, with every decision inspectable

**98 survey responses. 1,520 eligible roommate edges. Five matching strategies. One question: how many people can be placed without hiding the tradeoffs?**

A highest-score-first greedy allocator fills 40 rooms. CASPER's exact Blossom benchmark fills all 49 possible rooms on the same graph. Each extra room has a concrete explanation: an alternating path replaces one greedy pair with two eligible pairs.

![Greedy pairs P052 with P053. Blossom pairs each with an unmatched participant, P005 or P045, filling two rooms.](docs/coverage-example.svg)

In this four-response example, P052 and P053 have a strong 0.772 edge. Pairing P005 with P052 and P053 with P045 instead yields two valid rooms, with scores 0.704 and 0.582. CASPER extracts all nine disjoint paths that close the measured coverage gap.

## What makes CASPER distinctive

CASPER brings a preference model, an auditable allocation pipeline, and an optimization comparison together in one working project:

- **Compatibility and conflict are scored separately.** Eleven normalized preferences capture daily routines, while six interest indicators add Jaccard overlap. A symmetric conflict score models sleep, noise and visitors, snoring sensitivity, and irritability.
- **The graph represents real constraints.** Same-cohort and conflict-threshold checks determine eligible edges before matching. Every solver works on that same graph.
- **A fairness-aware C++17 allocator makes its tradeoffs explicit.** It uses a deterministic priority queue, then checks both two-pair reconnections. Its bounded refinement preserves the total score, protects the weaker affected pair, and reduces score variance. Unmatched people stay visible.
- **The benchmark has an exact reference.** Five strategies run on the same survey and constraints. The report records coverage, score, weakest pair, variance, and runtime so readers can see where heuristic speed and fairness trade against maximum-cardinality matching.
- **Every reported swap can be inspected.** The desktop replay records the before and after pairs, accepted score change, running total, and convergence. Alternating paths explain how a global reorganization creates extra rooms.

The contribution is this integrated, reproducible system and a direct evaluation on the supplied survey. The benchmark identifies which established algorithm wins each objective. CASPER does not claim a new general-purpose matching algorithm.

## Measured on the supplied survey

At conflict threshold **0.4** and penalty weight **0.5**, the model accepts **1,520 of 4,753** possible edges. Here is the observed comparison:

| Method | Rooms | Total adjusted score | Mean score | Weakest pair |
| --- | ---: | ---: | ---: | ---: |
| Seeded random feasible matching, mean of 200 runs | 42.00 | 21.252 | 0.506 | — |
| Score-first greedy | 40 | 28.413 | 0.710 | 0.385 |
| **CASPER C++ with fairness refinement** | **40** | **28.470** | **0.712** | **0.385** |
| Maximum-cardinality, maximum-weight Blossom | **49** | **31.642** | 0.646 | 0.284 |

On this run, **CASPER's C++ allocator improves total modeled score by 0.20% over score-first greedy**, with the same pair count and weakest-pair score. The exact Blossom reference raises coverage from 40 to 49 pairs, while accepting a lower mean and weakest score. The randomized baseline averages 42 pairs across its 200 trials. Total adjusted score reflects both pair quality and how many people are paired.

The separate desktop benchmark evaluates two local-search variants initialized from Blossom. Both preserve the exact matching score here, as expected when a two-pair swap must improve an already maximum-weight matching of the same size. Start from the greedy matching to see two genuine improving swaps instead.

These are outcomes of the stated scoring model, not measured roommate satisfaction. The survey has no follow-up outcomes for proposed pairs. [Full benchmark report](docs/benchmark.json) · [Survey analysis](docs/analysis.png) · [Scoring and refinement details](ALGORITHM.md)

## Run the desktop benchmark

With Python 3.10+ in an active virtual environment:

```sh
python -m pip install -r requirements-desktop.txt
python main.py --visualize
```

For a short demo:

1. Choose **Compare** to see all five methods.
2. Choose **Why coverage?** to trace a path that creates one additional room.
3. Choose **Switch start** until the display says **Greedy start**.
4. Press **Run** to replay the two accepted swaps and watch the score trace.

Press **Step** to advance one allocation at a time. **New data** samples up to 32 rows from the real survey and reruns the experiment.

Run the report and charts without opening the desktop window:

```sh
python main.py --seed 42 --trials 200
```

The command writes the machine-readable benchmark and five PNG figures to `results/`. Use `--data` with another validated survey CSV, `--threshold` to adjust conflict eligibility, or `--penalty` to adjust the conflict weight.

## What is being compared

| Strategy | Matching rule | Time after the shared score graph is built |
| --- | --- | --- |
| Random feasible | Shuffle eligible edges and accept disjoint pairs; report the trial mean | O(E) per trial |
| Score greedy | Accept eligible edges in descending weight order | O(E log E) |
| Blossom reference | Maximize cardinality, then score at that cardinality | O(N³) |
| Blossom with one swap pattern | Check one way to reconnect two pairs | O(N³ + I P²) |
| Blossom with both patterns | Check both eligible reconnections, then track each accepted change | O(N³ + I P²) |

`N` is the response count, `E` the eligible edge count, `P` the number of selected pairs, and `I` the bounded refinement passes. Score construction takes O(N²d), where `d` is the feature count. Reported matching times exclude that shared graph build. Random rows are trial means; the replay starts from one seeded draw.

The C++ fairness refinement and desktop swap experiments use distinct acceptance rules. The C++ allocator also protects the weaker pair and score variance. The desktop benchmark isolates the effect of checking one or both swap patterns. Keeping these experiments distinct makes the comparisons reproducible.

## The original allocation dashboard

The repository also includes the Streamlit interface for pair explanations, unmatched-participant review, preserving assignments as responses arrive, and exporting allocations. Run it with Python 3.12 and a C++17 compiler:

```sh
python -m pip install -r requirements.txt
python -m streamlit run NITW_Roommate_Optimizer/app.py
```

The public survey retains 98 response rows. Names, contact details, and direct identifiers were removed. Duplicate respondent rows are flagged in provenance and retained. [Dataset provenance](NITW_Roommate_Optimizer/data/provenance.json) · [Public measurements](NITW_Roommate_Optimizer/data/processed/participants.csv)

## Verify the project

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

GitHub Actions also runs the test suite, generates the desktop benchmark, and archives its report and figures. Read the [implementation scope](IMPLEMENTATION.md) and [deployment notes](DEPLOYMENT.md) for details.
