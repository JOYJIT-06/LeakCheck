# Checklist for reporting EEG decoding results (use it on your own pipeline)

1. What does the split estimate: new trials from the same runs, new runs, new sessions, new subjects? Say it in the paper.
2. Are any steps that use labels (CSP, feature or channel selection, tuning, scaling, augmentation) inside the training folds?
3. Do trials, windows or augmented copies of the same trial ever sit on both sides of a split?
4. Were the model settings (band, window, components, regulariser) chosen without looking at the test data?
5. Is there a negative control (same pipeline, shuffled labels) that returns chance?
6. Do you compare against a size-matched control, so training-set size is not mistaken for leakage?
7. Are label order and run structure reported (randomised or blocked)?
8. Is the chance threshold computed from independent test trials, and is that assumption stated?
9. Do you report trials per fold, per run and per subject, and the exclusion rules?
10. Is the unit of analysis the subject, and are repeats (seeds, folds) never counted as subjects?
11. Are code, versions, seeds, settings and a data dictionary released?
