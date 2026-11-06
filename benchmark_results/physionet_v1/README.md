# PhysioNet V1 benchmark outputs

These files are generated outputs from run `091e47dc`.

- Dataset: PhysioNet EEGMMIDB
- Participants completed: 105 of 106 requested
- Designs: D3_loro, D1m_matched_k, P1_csp_on_all
- Decoder: CSP + LDA
- CSP: MNE implementation, OAS regularisation
- Decoding band: 8–30 Hz
- Decoding window: 1–3 seconds
- Null procedures: within-run permutation and circular shift
- Null repetitions: 199 per type
- Seed: 42

The benchmark metadata records `emi` version 0.1.0. The public release
version is 1.0.0.

`subject_info.csv` has been sanitized by removing its machine-specific
`cache_file` column. No raw EEG recordings or cached epoch arrays are
included here.
