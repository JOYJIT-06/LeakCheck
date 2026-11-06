# Methods

## Dataset and participants

The V1 empirical benchmark used the PhysioNet EEG Motor Movement/Imagery
Database (EEGMMIDB). The selected motor-imagery runs were runs 4, 8, and
12. Event annotations T1 and T2 were mapped to the left- and right-hand
imagery classes according to the dataset event mapping used by the code.

The benchmark requested 106 participant IDs. Data processing and
benchmark evaluation completed for 105. Participant 86 was excluded
because only 24 eligible trials remained, below the configured minimum
of 30.

## Preprocessing

The implementation applies the following participant-level operations:

1. Band-pass filtering from 1 to 40 Hz.
2. Bad-channel detection using robust variance and correlation criteria.
3. Interpolation of detected bad channels when channel positions permit.
4. Average EEG reference.
5. ICA artifact correction. The component count is capped at 20 and
   constrained by the available rank. Frontal EEG channels Fp1/Fp2 are
   used as EOG proxies; at most two detected components are excluded.
6. Epoching from −1 to +4 seconds around the event.
7. Label-blind trial rejection using the configured adaptive artifact
   statistic and threshold rule.
8. Decoding-band filtering from 8 to 30 Hz and cropping to 1–3 seconds
   after the cue.

The cache retains a 0–4-second decoding-band interval so the analysis
can select windows within it. The V1 benchmark used the 1–3-second
window.

### Preprocessing limitation

Filtering, bad-channel handling, average reference, ICA fitting, and
trial-rejection threshold estimation are performed before cross-validation
and use all runs for that participant. These operations are label-blind,
but they are not fitted independently inside each training fold.
Consequently, V1 does not claim fully nested preprocessing. The
cross-validation split protects the classifier evaluation, but does not
make these preceding transformations independent of the held-out run.

## Decoder

The evaluated decoder was Common Spatial Patterns (CSP) followed by
Linear Discriminant Analysis (LDA). The benchmark used the MNE CSP
implementation with OAS regularisation and four CSP components.

## Validation designs

### D3: leave-one-run-out

Each run is held out in turn. The remaining runs are used for training.
This is the run-held-out reference design in V1.

### D1m: k-matched stratified random folds

The number of folds is set to the number of unique runs. For this
dataset, that is three folds. The split is stratified by class and
repeated according to the benchmark configuration. This design is
k-matched; it is not the separately implemented size-matched design D1s.

### P1: global-CSP positive control

CSP is fitted using all trials and labels before the classifier is
evaluated using leave-one-run-out splits. This deliberately allows
information from held-out labels to influence the spatial feature
transformation and serves as an injected-leakage positive control.

## Null models and statistics

The benchmark used two null procedures:

- `perm`: labels are permuted within runs.
- `shift`: labels are circularly shifted within runs.

There were 199 repetitions for each null type, with seed 42. The
benchmark configuration also recorded five ordinary repeats and
20 matched-design repeats.

Paired design differences, confidence intervals, Wilcoxon tests,
Holm-adjusted p-values, and effect sizes are provided in the generated
result tables. Null results must be interpreted relative to the
corresponding design and null procedure. A null accuracy need not equal
50% in every design.

## Software and reproducibility

The benchmark summary records `emi` 0.1.0, NumPy 2.5.4, SciPy 1.18.1,
scikit-learn 1.9.1, and MNE 1.13.2. The public software release is
`emi` 1.0.0; the benchmark results were generated with the earlier
recorded package version. Benchmark settings and summary files are
included in `benchmark_results/physionet_v1/`.
