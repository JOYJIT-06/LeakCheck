# Analysis plan (template: fill in, then FREEZE before the full run)

Register on OSF (or similar) after the pilot and before the full analysis. Edit nothing afterwards except in a dated amendment.

## Pilot
- Subjects used for the pilot: ______ (they are NOT part of the confirmatory set, or say so).
- SD of paired differences for the primary contrast: ______ pp  ->  subjects needed (scripts/analyze_leakcheck.py): ______

## Primary question
Within-subject inflation of accuracy when trials from the same run appear in both training and test data,
measured as Delta = accuracy(D1s size-matched random split) - accuracy(D3 leave-one-run-out), in percentage points.

## Fixed choices (do not tune on results)
Decoders: ______ | Primary decoder: ______ | Primary metric: pooled accuracy | Base window: 1-3 s | band 8-30 Hz
Designs and leaks included: ______ | Repeats: ______ | Null sets per subject: ______ | Seeds: ______
Technical exclusion rules (never by accuracy): >= 30 trials, >= 10 per class, >= 8 per run, 3 runs.
Datasets: ______ (licence and availability checked: yes/no)

## Smallest effect of interest and decision rules
Smallest effect of interest: ______ pp (justify). Equivalence margin for "no practical inflation": ______ pp.
Primary test: paired Wilcoxon on subject-level Delta, Holm-corrected within decoder family. Estimate: Hodges-Lehmann with BCa interval.
Dataset pooling: random-effects (DerSimonian-Laird), reporting tau^2, I^2 and a prediction interval.

## Hypotheses (write them in your own words, with the direction and the evidence that would refute them)
H1: ______   H2 (label autocorrelation moderates inflation): ______   H3: ______   H4: ______   H5: ______

## Exploratory (labelled as such)
Strata by accuracy tertile, mechanism diagnostics, any design not listed above.

## Deviations log
(date, what changed, why)
