# Contributing

- Run `pytest -q` before opening a pull request. New designs need tests that show they do what they claim
  (no index overlap, group isolation, correct sizes) and a test that shows a leak raises accuracy on pure noise.
- Keep all analysis choices in `src/emi/config.py` or as named constants in `leakcheck.py`.
- Never exclude subjects by accuracy. Technical exclusions only, and list them.
- Do not report synthetic-data output as a finding. It is software validation only.
- Good first contributions: leave-one-subject-out design (D7), filter-bank CSP, more datasets via the cache format,
  a beginner notebook, the ICA-on-all-data leak (P2) on raw recordings.
