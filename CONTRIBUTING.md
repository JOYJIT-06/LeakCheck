# Contributing to LeakCheck

Thank you for your interest in contributing to **LeakCheck**! We welcome contributions from computational neuroscientists, machine learning researchers, and scientific software engineers.

---

## 1. Code of Conduct and Scientific Principles

LeakCheck is an academic research software framework dedicated to scientific integrity, rigorous validation, and absolute reproducibility. All contributors must adhere to these foundational principles:

1. **Intellectual Honesty**: Never conceal negative results, null effects, or benchmark divergences. If a proposed decoder or validation design fails or degrades performance, document it transparently.
2. **Strict Grounding**: Every numerical result, table entry, or performance claim in the documentation or codebase must originate from executed code and logged telemetry. Never fabricate benchmark metrics or interpolate unmeasured values.
3. **No Metric-Based Exclusions**: Never exclude participants on the basis of classification accuracy or model performance. Participant exclusions are permitted strictly for documented technical reasons (e.g. corrupted files, missing metadata, hardware channel dropouts).
4. **Label-Blind Transformation Invariant**: Any preprocessing, filtering, channel interpolation, or decomposition applied to EEG signals must never access trial class labels.
5. **No Synthetic Findings**: Synthetic EEG data generators are reserved exclusively for software testing, unit tests, and CI verification. Synthetic outputs must never be reported as empirical scientific findings.

---

## 2. Development Workflow

### Setting Up a Development Environment
```bash
git clone https://github.com/JOYJIT-06/LeakCheck.git
cd LeakCheck
conda create -n leakcheck-dev python=3.10 -y
conda activate leakcheck-dev
pip install -e ".[dev]"  # or pip install -e . and pip install pytest
```

### Git Branching Conventions
- `main`: Stable release branch.
- Feature branches: `feat/<feature-name>` (e.g. `feat/new-bci-adapter`).
- Fix branches: `fix/<issue-name>` (e.g. `fix/covariance-conditioning`).
- Documentation branches: `docs/<topic>` (e.g. `docs/protocol-guide`).

### Conventional Commit Messages
Commits should adhere to conventional commit syntax:
- `feat:` A new capability, decoder, or dataset adapter.
- `fix:` A bug fix in algorithms, splitters, or CLI tools.
- `docs:` Documentation improvements or scientific guides.
- `test:` Adding or refining automated tests.
- `refactor:` Code improvements without behavioral alterations.

---

## 3. Testing and Quality Standards

### Running the Test Suite
Before submitting any pull request, ensure all tests pass cleanly:
```bash
pytest tests -q
```
All 186 tests must pass. If adding a new feature or design:
1. Include unit tests demonstrating index isolation ($\mathcal{I}_{\text{train}} \cap \mathcal{I}_{\text{test}} = \emptyset$).
2. Include a synthetic noise test verifying that supervised leakage intentionally raises accuracy above chance, whereas clean designs remain at chance level.
3. Verify that your code compiles cleanly under Python 3.10+ without syntax errors or unhandled warnings.

---

## 4. Submitting a Pull Request

1. Fork the repository and create your feature branch.
2. Commit your changes with clear, descriptive commit messages.
3. Push to your fork and submit a Pull Request to `JOYJIT-06/LeakCheck`.
4. Describe the scientific rationale, mathematical design, and include test verification logs in the PR description.
