# V1 requirements and validation status

| Requirement | V1 status | Notes |
|---|---|---|
| PhysioNet EEGMMIDB loader | Evaluated | 105 participants completed |
| MOABB adapter | Experimental | Not validated in V1 |
| CSP + LDA decoder | Evaluated | MNE CSP, OAS regularisation |
| D3 leave-one-run-out | Evaluated | Reference design |
| D1m k-matched stratified folds | Evaluated | Three folds for three runs |
| D1s size-matched design | Not evaluated | Implemented separately |
| P1 global-CSP leakage control | Evaluated | Deliberate positive control |
| Permutation null | Evaluated | 199 repetitions |
| Circular-shift null | Evaluated | 199 repetitions |
| OpenBMI | Not evaluated | Future validation |
| Multi-dataset validation | Not completed | Future work |
| Multi-site validation | Not completed | Future work |
| Fully fold-nested preprocessing | Not implemented in V1 | Label-blind preprocessing uses all runs |

## Test status

The local V1 development environment previously passed 87 tests.
Run the test suite again from the release checkout before publication.

## Interpretation

Implemented code paths are not automatically empirically validated.
The empirical claims in V1 are restricted to the dataset, decoder,
designs, and null procedures listed above.
