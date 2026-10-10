# Implementation scope

This implementation follows Project III (CASPER), retaining the supplied ZIP's Python modules and scoring model while replacing its primary matcher with the report's C++ heap-and-refinement pipeline.

| Requirement | Implementation |
| --- | --- |
| Collect and preprocess preferences | Validates all 98 original response rows, scales eleven numeric features, encodes original interest categories |
| Compatibility score | Original 0.6 numeric similarity + 0.4 Jaccard interest model |
| Conflict score | Original ZIP interactions, corrected by averaging forward and reverse directions |
| Nonlinear adjustment | `CS − λ CF²`, with visible controls and per-pair decomposition |
| Constraint-aware graph | Same supplied hostel cohort; configurable conflict pruning |
| Priority-queue selection | Native C++17 maximum heap with deterministic ties |
| Local pair optimization | Both alternative two-pair swaps, eligibility checks, bounded passes |
| Fairness / equilibrium | Total-score protection, weakest-pair protection and nonincreasing variance during unlocked refinement |
| Comparison and analysis | Actual heap greedy, CASPER and exact Blossom measurements on identical eligible edges |
| Room allocation | Exports pairing IDs; accepts real room inventory for room assignment |
| Notifications | Administrator-only reviewed SMTP delivery using private addresses and secrets |
| Visual demonstration | Native Streamlit UI, Plotly networks/radars/matrices, Matplotlib/Seaborn figure export |
| Online matching | Append actual responses; preserve pairs or recompute; validate locks against constraints |
| Adaptive scoring | Measured nine-value λ sensitivity analysis and an explicit recommendation policy |
| Machine-learning extension | Evaluated data readiness; supervised pair prediction deferred because linked outcomes are absent |
| Deployment | Streamlit Community Cloud dependencies, compiler package, configuration and GitHub Actions |

## Deliberate corrections

The source algorithm could reintroduce pruned edges during swaps and only checked one alternate pairing. The C++ engine validates both alternatives against the same eligible graph. Pass limits make computational claims explicit. Directional conflict is symmetrized, and the original scoring weights are preserved rather than substituting the report's separate illustrative feature model.

Results, solver timings and room assignments are not hardcoded. Unmatched participants remain visible; no fallback overrides constraints. The source contains 98 rows, regardless of the report's broader survey-count statement. Repeated respondent identifiers are flagged, not silently removed.

## Limits

Fairness is measured over pair scores, not demographic parity or individual utility. It is a local improvement constraint and does not prove an equilibrium. Preserving online pairs restricts fairness refinement to the unlocked pool. CASPER does not prove optimal weight, maximum matching cardinality or stable-roommate preferences.

The app retains the ZIP's Male/Female hostel partitions and numeric coding without inventing extra constraints or questionnaire anchors. Real institutional allocation requires human review and actual room inventory. Individual satisfaction is available for description but cannot label the success of newly proposed pairs.

Session updates and email retry records do not survive a restart. There is no database in the supplied stack. The optional FastAPI module is stateless and needs a separate server deployment if it is to be public. Public data contains pseudonyms, not an assurance that detailed survey responses are impossible to reidentify.
