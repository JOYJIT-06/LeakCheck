# Validation designs and leakage controls

## Validation designs

- **D1:** shuffled k-fold validation.
- **D2:** stratified shuffled k-fold validation.
- **D1m:** stratified random k-fold validation where k equals the number
  of runs. This is the k-matched design evaluated in V1.
- **D1s:** separately implemented size-matched random validation. It
  was not evaluated in the V1 benchmark.
- **D3:** leave-one-run-out validation. This is the V1 run-held-out
  reference design.
- **D4 / D4b:** chronological holdout and forward-chaining designs.
- **D6:** leave-one-session-out design when session groups are available.

## Injected leakage

- **P1:** fit CSP on all trials and labels before cross-validation.
  Evaluated in V1 as a deliberately contaminated positive control.
- **P3:** global scaling versus fold-contained scaling.
- Other injected leakage mechanisms are implemented or documented
  separately; their presence in the code does not mean they were
  empirically evaluated in V1.

## Null models

- **Permutation:** permute labels within each run.
- **Circular shift:** circularly shift labels within each run.

The V1 benchmark used 199 repetitions for each null type.

## V1 empirical scope

The V1 empirical benchmark used PhysioNet EEGMMIDB, CSP + LDA, and
three designs: D3, D1m, and P1. It completed for 105 participants.
The evaluated decoding band was 8–30 Hz and the decoding window was
1–3 seconds.

The D1m comparison is k-matched, not D1s size-matched. D1s was not
included in the reported V1 benchmark.

## Interpretation

The P1 design deliberately fits CSP using held-out labels and is
expected to demonstrate optimistic leakage. Its results are a positive
control, not a valid deployment estimate.

D1m and P1 null rates should not be described as clean-design false
positive rates. The D3 null rate is the clean run-held-out reference
false-positive rate for this experiment.

Preprocessing was performed before cross-validation using all runs.
Although the preprocessing rules are label-blind, they are not fully
fold-nested. This limitation must be considered when interpreting
run-held-out estimates.

## Validation status

- PhysioNet EEGMMIDB: empirically evaluated in V1.
- MOABB adapter: experimental; not validated by V1.
- OpenBMI: not evaluated in V1.
- Multi-dataset validation: not completed.
- Multi-site validation: not completed.
