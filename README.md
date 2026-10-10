<p align="center"><img src="site/icon.svg" width="64" alt="CASPER logo"></p>
<h1 align="center">CASPER · Room for better matches.</h1>
<p align="center">An explainable roommate matching studio.<br>Designed and rebuilt by <strong>ASHRITH RAJU</strong>.</p>
<p align="center"><a href="https://ashrith-r.github.io/casper-roommate/">Explore the live demo ↗</a> · <a href="DEPLOYMENT.md">Deploy your own</a> · <a href="ALGORITHM.md">Understand the model</a></p>

---

Good roommates start with understanding how people live. CASPER turns survey preferences into transparent pairing suggestions, balancing shared routines with potential friction.

This independent web rebuild grows out of a **group design-thinking project**. It replaces the lost local implementation with an interactive, deployable product and documents the assumptions behind its model. The original group repository and survey schema are credited in [CREDITS.md](CREDITS.md).

## The experience

- A responsive matching studio with a connection map and individual pair explanations.
- Adjustable conflict penalties and exclusion limits, with explicit stale-result indicators.
- CSV import supporting the original raw survey headings and processed normalized columns.
- Manual student profiles, search, sorting, and downloadable matching reports.
- Clear visibility for unmatched students and the lowest pair score.
- A design-thinking case study and an honest explanation of the heuristic.
- Browser-local processing: no backend, API keys, analytics, or database.

The included **16 demo profiles are entirely fictional**. Original respondent data is deliberately excluded. Uploaded data exists in page memory and disappears on refresh; exporting a report saves it to your device. Google Fonts provides optional typography and receives normal font requests, but no survey data. System fonts are the fallback.

## Run locally

Install [Node.js 22 or newer](https://nodejs.org/), then:

```sh
git clone https://github.com/ashrith-r/casper-roommate.git
cd casper-roommate
node scripts/serve.mjs
```

Open **http://127.0.0.1:4173**. No package installation is required. Do not open `index.html` directly from the filesystem: JavaScript modules need an HTTP server.

```sh
node --test tests/*.test.mjs
```

## Bring survey responses

1. Open **Students → Template** to download an example CSV.
2. Use numeric values from **0–10** for cleanliness, sleep routine, social energy, snoring frequency and snoring sensitivity. Interests are comma-separated inside a quoted CSV field.
3. Choose **Original survey / template · 0–10**, or **Normalized / processed data · 0–1** for normalized columns.
4. Leave **Replace names with student labels** enabled for a pseudonymous demonstration.
5. Select **Choose CSV**. Import replaces the cohort only after validation succeeds.
6. Return to **Matching studio**, run matching, inspect explanations, and export the CSV.

```csv
name,cleanliness,sleep_time,social,snore_freq,snore_sensitivity,hobbies
Student 001,8,7,5,2,4,"Coding,Music"
Student 002,9,8,6,1,5,"Coding,Music"
```

The importer supports `Full Name`, the source typo `Cleaniliness`, `Sleep Time`, the original social/snoring question headings, and `hobbies_raw`. Normalized imports prefer `*_norm` columns. Unused fields, including emails, are discarded. Missing required scores and out-of-range values cause a clear error instead of silent imputation. Repeated names are flagged for review, with every row preserved under a unique ID; named imports append row numbers to repeated labels. Check for duplicate submissions yourself before using matches. Cohorts are capped at **200 people / 2 MB** for this browser prototype.

**Interpretation matters:** original form scale descriptions are not included in the source repository. Verify the meaning of the input numbers before using real responses. In the new manual form, low→high means relaxed→tidy, early→late sleep preference, quiet→social, never→often snoring, and low→high snoring sensitivity. Sleep is ordinal, not circular clock time.

## How matching works

```text
Survey CSV / student profiles
  → validate and normalize
  → compatibility − λ × conflict²
  → remove invalid or non-positive edges
  → greedy selection in descending score order
  → constrained two-pair swaps (at most 10 passes)
  → pairs, explanations and unmatched students
```

The browser version uses **JavaScript ES modules** to run directly on GitHub Pages. It is a fresh implementation of the supplied C++ prototype’s idea, with corrected symmetric conflict semantics, both swap alternatives, constraint checks during refinement and a fixed iteration budget.

With a fixed feature set, time is **O(n² log n + Pn²)**, P ≤ 10, and memory is **O(n²)**. It is a heuristic: no near-optimality, maximum cardinality, stable-roommate, fairness, or real-world satisfaction guarantee is claimed. Scores are model values, not success probabilities. See [ALGORITHM.md](ALGORITHM.md).

## Design-thinking process

| Stage | Project focus |
| --- | --- |
| Empathize | The group collected form responses about living habits and preferences. |
| Define | Identify interpretable similarities and likely sources of conflict. |
| Ideate | Balance compatibility with a nonlinear conflict penalty. |
| Prototype | Build a usable matching studio that exposes its reasoning. |
| Test next | Validate questionnaire anchors, compare with exact matching, collect consented feedback and evaluate actual outcomes. |

This repository does not invent participant counts, feedback quotes, user-study results or satisfaction improvements.

## Repository map

```text
site/                  Deployable static app
  index.html           Dashboard, student management, method and project story
  styles.css           Responsive visual design
  app.js               Interface state and interactions
  engine.js            Scoring and constrained matching
  data.js              Demo cohort, CSV parsing and survey mapping
  template.csv         Fictional import example
tests/                 Built-in Node tests; no test dependencies
scripts/serve.mjs       Local preview server
.github/workflows/     Tests and GitHub Pages deployment
```

## Scope and next steps

This is a student project and discussion tool. Review suggested pairs with students before using them. It does not enforce room capacity, eligibility, mutual choices, hostel policies, or safeguarding requirements. Explicit fairness objectives, calibrated survey weights, exact-matching benchmarks, unmatched-student augmentation and consented longitudinal evaluation are possible next steps.

## Credits

Redesign and web implementation: **ASHRITH RAJU** ([ashrith-r](https://github.com/ashrith-r)).

Group-project reference: [CASPER-Roommate-System / NITW_Roommate_Optimizer](https://github.com/chitranshpriyanshu/CASPER-Roommate-System/tree/main/NITW_Roommate_Optimizer). Original group member names should be added when confirmed; this rebuild does not claim sole authorship of the group concept. See [CREDITS.md](CREDITS.md) for provenance and reuse notes.
