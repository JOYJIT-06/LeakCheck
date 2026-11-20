# V1.1 Preprocessing and Validation Limitations

**Status:** Documentation correction for the frozen PhysioNet V1.1 analysis  
**Scope:** Methodological interpretation only; no benchmark values or source-code behavior are changed by this document.

## 1. What the implementation does

The PhysioNet subject pipeline in `src/emi/pipeline.py` performs these operations in this order:

1. Load the selected runs for one participant into a subject recording.
2. Call `preprocess.clean_raw(raw, cfg)`.
3. Call `preprocess.build_epochs_full(raw_clean, cfg)`.
4. Extract the preprocessed decoding data and labels.
5. Evaluate run-held-out and random-trial validation designs on that feature array.

The preprocessing functions perform filtering, bad-channel detection/interpolation, average referencing, ICA, label-blind trial rejection, and decoding-band epoch construction before the cross-validation routines receive the data. The preprocessing docstring in `src/emi/preprocess.py` explicitly states that these operations use all runs, including the run later held out.

## 2. What is and is not fold-nested

| Component | Boundary in the described pipeline |
|---|---|
| Filtering and continuous-signal preprocessing | Subject-level, before validation folds |
| Bad-channel detection/interpolation | Subject-level, before validation folds |
| Average reference | Subject-level, before validation folds |
| ICA fitting/component exclusion | Subject-level, before validation folds |
| Adaptive label-blind trial rejection | Estimated/applied before validation folds |
| CSP feature transformation | Fitted within each decoding training fold |
| LDA/classifier | Fitted within each decoding training fold |
| P1 positive control CSP | Deliberately fitted using all trials and labels before D3 splitting |

Accordingly, the clean validation designs are **fold-nested at the supervised decoding stage**, but are **not fully raw-to-prediction fold-nested**.

## 3. Consequences for interpretation

The D3, D1m, and D1s scores are conditional on a shared subject-level preprocessed representation. The comparison evaluates different trial-partitioning strategies after that preprocessing has already used all selected runs.

This does not make the preprocessing equivalent to P1: the preprocessing operations described above are label-blind, whereas P1 uses class labels to fit CSP before splitting. Nevertheless, using the held-out run during preprocessing means the clean validation pipeline does not reproduce a strict setting in which every data-dependent preprocessing parameter is estimated using only the training runs.

Therefore:

- Do not describe the complete preprocessing-and-decoding pipeline as fully nested.
- Do not claim that D3 is an untouched raw-data holdout.
- Do not attribute all observed differences exclusively to split granularity without acknowledging the shared preprocessing boundary.
- Do not interpret the results as a complete test of deployment-time generalization where preprocessing must be learned from training data only.
- Preserve the existing benchmark values as results from the documented pipeline; do not silently relabel them as results from a fold-nested raw-data pipeline.

## 4. P2 status

The current preprocessing implementation does fit ICA using all selected runs. However, the dedicated P2 experiment requires a controlled comparison between this global preprocessing and a genuinely fold-nested raw-data preprocessing implementation. The module header in `src/emi/leakcheck.py` identifies P2 as requiring raw recordings and as not included in that module.

Thus, the presence of global ICA in preprocessing is not, by itself, evidence that the P2 effect has been experimentally quantified. P2 must remain marked as not yet evaluated until the matched clean-versus-contaminated experiment is implemented and validated.

## 5. Required future correction for a fully nested pipeline

A future, separately versioned experiment may implement raw-data fold nesting:

1. Split raw runs/trials first according to the validation design.
2. Fit every data-dependent preprocessing operation using training data only.
3. Apply the fitted preprocessing parameters to the held-out data without refitting.
4. Fit CSP and the classifier on the transformed training data only.
5. Record trial retention, bad channels, ICA components, and fold-level preprocessing metadata.
6. Compare the new pipeline against the existing V1.1 result as a distinct analysis.

This would change the evaluated pipeline and may change trial retention and accuracy. It must therefore be treated as a new benchmark version, not as a documentation-only correction or a replacement of the frozen V1.1 results.

## 6. Preservation statement

This correction does not modify source-code behavior, participant inclusion, validation splits, decoders, frozen CSVs, figures, or reported accuracy values. It corrects the description and limits the claims to what the implementation supports.
