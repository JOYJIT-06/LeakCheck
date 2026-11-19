# LEAKCHECK V1.1 — EXHAUSTIVE SCIENTIFIC AND SOFTWARE AUDIT

## 0. MISSION

Perform an exhaustive, evidence-based audit of LeakCheck V1.1.

This is the PhysioNet EEGMMIDB single-dataset release only.

The objective is to discover every:
- Incorrect result.
- Numerical discrepancy.
- Contradictory report.
- Scientific error.
- Statistical error.
- Implementation defect.
- Missing experiment.
- Unsupported interpretation.
- Manuscript inconsistency.
- Reproducibility failure.
- Release or packaging issue.
- Unsupported completion claim.

Compare every important finding with earlier audit reports, the current manuscript, previous status reports, the existing claim-evidence matrix, and primary evidence.

Do not assume the previous audit is correct.
Do not assume the latest report is correct.
Do not assume the Consensus report is correct.
Determine what the actual evidence supports.

## 1. PROJECT LOCATIONS

Repository:
D:\my lab\LeakCheck_remote

Manuscript:
D:\my lab\LeakCheck_Manuscript_Local\V1_PhysioNet

Expected branch:
research/v1.1-final-audit

Previously reported local HEAD:
2774aa9

Previously reported remote HEAD:
4c63b27

Expected release tag:
v1.1.0

All of these identifiers must be checked against the actual repository.

Audit output directory:
THIS RUN'S CURRENT DIRECTORY, containing MASTER_AUDIT_INSTRUCTIONS.md.

Only create or edit files inside this audit output directory.

## 2. NON-NEGOTIABLE SAFETY RULES

READ-ONLY AUDIT.

Do not:
- Edit source code.
- Edit tests.
- Edit configuration.
- Edit raw EEG data or cache.
- Edit manuscript.md.
- Edit references.bib.
- Edit publication figures.
- Change package metadata.
- Install dependencies.
- Upgrade Python or packages.
- Switch branches.
- Commit.
- Push.
- Tag.
- Reset.
- Rebase.
- Merge.
- Modify main.
- Modify v1.1.0.
- Modify v2-dev.

Do not silently repair discrepancies.

If a correction is necessary, report the exact file, line, proposed correction and reason. Do not apply it.

If an experiment is missing, report it as missing. Do not fabricate an output.

If a tool or agent fails, record the failure. Do not count it as completed work.

Never claim 100% verification merely because an audit script ran.

## 3. TEAM STRUCTURE

Create five master auditor roles and one independent chief scientific auditor.

MASTER 1:
Repository, software, tests, package, release, Git provenance.

MASTER 2:
PhysioNet raw data, EDF provenance, preprocessing, participant flow and cache.

MASTER 3:
EEG scientific methods, signal processing, machine learning, CSP, leakage mechanisms and experimental design.

MASTER 4:
Statistical validation, participant-level estimates, bootstrap, confidence intervals, hypothesis testing, R replication and reproducibility.

MASTER 5:
Manuscript, figures, references, claim-evidence mapping, novelty, scientific interpretation and preprint readiness.

CHIEF SCIENTIFIC AUDITOR:
Independent Head Reviewer. Challenge all five master reports. Resolve disagreements using primary evidence. Do not accept a master's conclusion without independent inspection.

The chief reviewer is an audit role, not a claim of medical or clinical credentials.

## 4. 100 DISTINCT SUB-AUDIT WORK PACKAGES

Create a ledger with exactly 100 uniquely identified work packages.
Assign 20 packages to each master auditor.

Use concurrent subagents where available. Use staged batches or Dynamic Workflows where supported.

Do not attempt uncontrolled recursion.
Do not create duplicate tasks merely to increase agent count.
Do not claim 100 agents launched unless the agent manager confirms that number.

Each package must have:
- Unique ID.
- Assigned master.
- Specific question.
- Required primary evidence.
- Verification method.
- Output.
- Status: NOT_STARTED, RUNNING, COMPLETED, FAILED, KILLED or BLOCKED.
- Reviewer identity.

### MASTER 1 — SOFTWARE AND REPOSITORY (W01-W20)

W01: Verify repository path and repository identity.
W02: Verify current branch and branch tracking.
W03: Verify local and remote HEAD commits.
W04: Verify commit 2774aa9 and its contents.
W05: Verify commit 4c63b27 and its contents.
W06: Verify v1.1.0 tag and target commit.
W07: Inspect complete release commit history.
W08: Verify main branch protection and baseline integrity.
W09: Verify v2-dev isolation without modifying it.
W10: Inspect working-tree changes and untracked files.
W11: Verify package version and project metadata.
W12: Verify actual production module inventory.
W13: Verify absence of V2/OpenBMI code in release package.
W14: Verify licence consistency and provenance.
W15: Verify dependencies and supported Python versions.
W16: Inspect test suite structure and test discovery.
W17: Run tests only in a suitable existing environment.
W18: Verify wheel contents and SHA-256.
W19: Verify sdist contents and SHA-256.
W20: Verify clean-environment installation feasibility and package smoke tests.

### MASTER 2 — DATA AND PARTICIPANT FLOW (W21-W40)

W21: Identify the original PhysioNet EEGMMIDB source.
W22: Verify raw EDF file provenance.
W23: Verify available participant directories.
W24: Reconstruct requested participant count.
W25: Reconstruct successfully downloaded participant count.
W26: Reconstruct processed participant count.
W27: Reconstruct final retained participant count.
W28: Investigate S044 exclusion.
W29: Investigate S069 exclusion.
W30: Investigate S091 exclusion.
W31: Investigate S086 exclusion.
W32: Check historical S088 exclusion claim.
W33: Check historical S092 exclusion claim.
W34: Check historical S100 exclusion claim.
W35: Check historical S104 exclusion claim.
W36: Verify sampling-rate counts and their cohort denominator.
W37: Verify channel count and channel consistency.
W38: Verify trial counts, event labels and run structure.
W39: Verify epoch rejection thresholds and actual rejection logs.
W40: Reconcile raw files, cache, manifests and result tables.

### MASTER 3 — SCIENTIFIC METHODS AND IMPLEMENTATION (W41-W60)

W41: Verify filtering implementation and filter order.
W42: Verify filter phase, padding and edge handling.
W43: Verify sampling-rate handling and resampling.
W44: Verify epoch boundaries and time indices.
W45: Verify baseline implementation.
W46: Verify artifact rejection and peak-to-peak threshold.
W47: Verify channel handling and rank estimation.
W48: Verify covariance estimator implementation.
W49: Verify OAS covariance and shrinkage settings.
W50: Verify CSP component count and fit/transform logic.
W51: Verify whether CSP sees held-out trials.
W52: Verify whether CSP sees held-out labels.
W53: Verify feature extraction and normalization.
W54: Verify LDA implementation and regularization.
W55: Verify fold nesting and data isolation.
W56: Verify D3 LORO implementation.
W57: Verify D1s split implementation.
W58: Verify D1m split implementation.
W59: Verify P1 global-CSP contamination implementation.
W60: Verify P3-P9 mechanisms and distinguish implementation from executed experiments.

### MASTER 4 — STATISTICS AND REPRODUCIBILITY (W61-W80)

W61: Locate participant-level primary result data.
W62: Recalculate P1 versus D3.
W63: Recalculate D1s versus D3.
W64: Recalculate D1m versus D3.
W65: Recalculate D1s versus D1m.
W66: Verify Hodges-Lehmann estimator definition.
W67: Verify paired participant matching.
W68: Verify confidence interval calculation.
W69: Verify BCa bootstrap implementation.
W70: Verify B=2,000 versus B=10,000 discrepancy.
W71: Verify random seed and resampling reproducibility.
W72: Verify raw Wilcoxon p-values.
W73: Verify Holm-Bonferroni adjustment.
W74: Verify Cohen's dz.
W75: Verify rank-biserial effect sizes.
W76: Verify TOST margins, hypotheses and conclusion.
W77: Verify permutation and shift null experiments actually ran.
W78: Inspect independent R implementation.
W79: Reconcile Python and R outputs from primary data.
W80: Verify all reported statistical outputs against saved files.

### MASTER 5 — MANUSCRIPT AND SCIENTIFIC CLAIMS (W81-W100)

W81: Inventory complete manuscript and supporting guides.
W82: Reconcile abstract values with primary outputs.
W83: Reconcile Methods with executable code.
W84: Reconcile Results with participant-level outputs.
W85: Reconcile tables with figures.
W86: Verify all figure formats and underlying plotted data.
W87: Check all bibliography entries and metadata.
W88: Check citation-to-claim scientific support.
W89: Inspect novelty and priority claims.
W90: Check single-dataset V1.1 scope compliance.
W91: Check all leakage terminology and definitions.
W92: Check D3 operational-reference wording.
W93: Check P1 causal interpretation and held-out label access.
W94: Check D1s versus D1m interpretation.
W95: Check null and negative-result reporting.
W96: Check speculation versus measured findings.
W97: Check limitations and generalization claims.
W98: Check reproducibility and software availability statements.
W99: Compare current manuscript with previous audit versions.
W100: Produce the manuscript correction matrix and preprint checklist.

## 5. TEN VERIFICATION PASSES

Every critical claim must undergo these ten distinct passes.
Record which passes apply to each claim.

PASS 1 — INVENTORY:
Find the claim in the manuscript, reports, tables and code.

PASS 2 — PRIMARY SOURCE:
Locate the underlying source code, raw data, logs or participant-level output.

PASS 3 — IMPLEMENTATION:
Trace the actual implementation, not just its documentation.

PASS 4 — NUMERICAL REPRODUCTION:
Recalculate the result independently where possible.

PASS 5 — CROSS-ARTIFACT COMPARISON:
Compare manuscript, CSV, R output, figures, audit reports and previous versions.

PASS 6 — HISTORICAL COMPARISON:
Check whether previous reports contradict the latest report.

PASS 7 — SCIENTIFIC VALIDITY:
Evaluate whether the method, statistical test and interpretation are appropriate.

PASS 8 — ADVERSARIAL FALSIFICATION:
Attempt to disprove the claim using counterexamples, alternate explanations and independent checks.

PASS 9 — REPRODUCIBILITY:
Check whether another analyst could reproduce the result from the recorded inputs, code, configuration and environment.

PASS 10 — INDEPENDENT SIGN-OFF:
Chief Scientific Auditor reviews the evidence and assigns a final disposition.

A claim cannot be labelled VERIFIED simply because all ten passes were written down. The actual evidence must support it.

## 6. SPECIFIC DISCREPANCIES THAT MUST BE INVESTIGATED

### 6.1 Statistical contradictions

Previously reported:
P1 versus D3:
HL +24.50 pp
95% BCa CI [+21.75, +27.78]
Wilcoxon p=1.48e-18
Cohen's dz=+1.771
rank-biserial=+0.998

D1s versus D3:
HL -2.68 pp
95% BCa CI [-3.94, -1.46]
p=5.86e-05
dz=-0.449
rank-biserial=-0.452

D1m versus D3:
HL -4.47 pp
95% BCa CI [-5.80, -3.11]
p=5.41e-09
dz=-0.685
rank-biserial=-0.659

D1s versus D1m:
HL +1.86 pp
95% BCa CI [+1.27, +2.50]
p=2.64e-07

These are reported values, not accepted ground truth.

Investigate:
- Conflicting CI endpoints in earlier manuscript versions.
- Bootstrap B=2,000 versus B=10,000.
- Bootstrap seed.
- Raw versus Holm-adjusted p-values.
- Whether reported effect sizes are based on the correct paired differences.
- Whether the paired HL estimator and marginal accuracy summaries are clearly distinguished.

The displayed P1 accuracies 60.15% and 84.97% differ by 24.82 pp. The paired HL estimate is +24.50 pp. This is not automatically an error, but the underlying distributions and estimator definitions must be checked.

### 6.2 Participant flow

Previously reported:
109 requested.
105 retained.
3 excluded for bad channels >15%: S044, S069, S091.
1 excluded for insufficient trials: S086.

A previous report said 106 participants at 160 Hz and 3 at 128 Hz.

Verify whether those sampling-rate counts describe the requested cohort or the retained cohort.

Investigate historical contradictions about S091's exclusion reason.

### 6.3 Mechanism classification

For each P1-P9, classify:
- Designed.
- Implemented.
- Unit tested.
- Tested on synthetic data.
- Executed on PhysioNet.
- Saved empirical output.
- Independently reproduced.
- Reported in manuscript.

Do not confuse these statuses.

Investigate whether null experiments were actually executed or only implemented.

### 6.4 Scientific interpretation

Check:
- D3 is an operational reference protocol, not deployment ground truth.
- A non-significant TOST result does not prove non-equivalence.
- D1s versus D1m is a protocol contrast, not an isolated causal fold-geometry effect.
- Negative D1s/D1m contrasts must not be described as inflation above D3.
- P1 contamination must be supported by actual held-out label access.
- A difference between marginal medians need not equal the paired HL shift.
- Physiological explanations such as electrode contact or cognitive state are speculative unless directly measured.
- Implementation is not evidence of empirical validation.
- Reference resolution is not evidence that a citation supports the claim.

### 6.5 Earlier Consensus critique

Investigate every concern from the supplied Consensus assessment:

1. Absolute zero-discrepancy audit language.
2. Claims of 100% numerical consistency.
3. CI endpoint conflicts.
4. D1s/D1m protocol contrast interpretation.
5. P1 mechanism and held-out label access.
6. Participant-flow certification.
7. Unsupported claims that historical errors were refuted.
8. Unsupported claims that all V2 material was purged.
9. Citation resolution versus actual source support.
10. Missing or unreadable evidence attachments.

Do not accept Consensus assertions automatically. Verify each concern independently.

## 7. REQUIRED SCIENTIFIC VALIDATION

This is a scientific benchmark, not merely a software package audit.

Review:
- EEG dataset suitability.
- Motor-imagery task and event definition.
- Participant/run/trial structure.
- Sampling rate and temporal resolution.
- Filter design and phase characteristics.
- Epoching and baseline.
- Artifact rejection.
- Channel selection and rank.
- Covariance estimation.
- CSP mathematical formulation and fitting scope.
- Log-variance features.
- LDA assumptions and regularization.
- Cross-validation independence.
- Run-wise versus trial-wise generalization.
- Subject-specific scope.
- Leakage definitions.
- Distinction between partitioning and supervised contamination.
- Statistical estimands.
- Paired comparisons.
- Bootstrap methodology.
- Multiple-comparison control.
- Effect-size interpretation.
- Null controls.
- TOST assumptions and margins.
- Reproducibility and data provenance.
- External validity and limitations.

Check whether the methods are consistent with relevant primary literature and established EEG/BCI methodology.

For each scientific concern, cite the exact source or paper and explain what it supports. Do not invent references or claim consensus without evidence.

Use the browser/research capability for external literature verification where available. Separate external literature evidence from local project evidence.

## 8. PREVIOUS REPORT COMPARISON

Search and inspect all earlier relevant audit reports, including:
- LOCAL_V1_1_INDEPENDENT_SCIENTIFIC_AUDIT.md
- V1_1_FINAL_QUALITY_GATES.md
- V1_1_FINAL_REPORT.md
- V1_1_SOFTWARE_TEST_REPORT.md
- V1_1_STATISTICAL_VALIDATION.md
- V1_1_FINAL_SCIENTIFIC_VALIDATION.md
- V1_1_REFERENCE_AUDIT.md
- V1_1_FIGURE_AUDIT.md
- V1_1_PARTICIPANT_FLOW_AUDIT.md
- V1_1_EXPERIMENTAL_DESIGN_AUDIT.md
- V1_1_DECODER_PREPROCESSING_AUDIT.md
- CLAIM_EVIDENCE_MATRIX.md
- V1_1_SCOPE_COMPLIANCE_REPORT.md

Also inspect the manuscript-local claim-evidence matrix and earlier evidence guides.

For each previous claim, determine:
- Confirmed.
- Contradicted.
- Partially supported.
- Superseded.
- Not independently verified.

Create a previous-versus-current comparison table.

## 9. OUTPUT FILES — MUST BE SAVED LOCALLY

Create all files inside this run's audit directory.

Required:

00_EXECUTIVE_SUMMARY.md
01_AUDIT_SCOPE_AND_METHOD.md
02_REPOSITORY_AND_RELEASE_AUDIT.md
03_SOFTWARE_AND_TEST_AUDIT.md
04_DATA_PROVENANCE_AUDIT.md
05_PARTICIPANT_FLOW_AUDIT.md
06_EEG_PREPROCESSING_AUDIT.md
07_DECODER_AND_CSP_AUDIT.md
08_EXPERIMENTAL_DESIGN_AUDIT.md
09_P1_TO_P9_MECHANISM_MATRIX.md
10_STATISTICAL_RECALCULATION_AUDIT.md
11_BOOTSTRAP_AND_CONFIDENCE_INTERVAL_AUDIT.md
12_HYPOTHESIS_TESTING_AND_EFFECT_SIZE_AUDIT.md
13_PYTHON_R_INDEPENDENT_REPLICATION.md
14_NULL_EXPERIMENT_AUDIT.md
15_MANUSCRIPT_TO_CODE_CONGRUENCE.md
16_FIGURE_AND_TABLE_AUDIT.md
17_REFERENCE_AND_CITATION_SUPPORT_AUDIT.md
18_SCIENTIFIC_VALIDITY_AND_NOVELTY.md
19_PREVIOUS_AUDIT_COMPARISON.md
20_CONSENSUS_CRITIQUE_RESOLUTION.md
21_RELEASE_AND_REPRODUCIBILITY_AUDIT.md
22_ALL_DISCREPANCIES_AND_CORRECTIONS.md
23_PREPRINT_READINESS_VERDICT.md
24_TEN_PASS_VERIFICATION_MATRIX.md
25_100_WORK_PACKAGE_COMPLETION_LEDGER.md
26_AGENT_FAILURE_AND_QUOTA_LOG.md
27_FINAL_CHIEF_SCIENTIFIC_AUDITOR_SIGNOFF.md

Also save:
- All five master reports.
- Each sub-audit result.
- Exact commands executed.
- Test logs.
- Statistical recalculation outputs.
- Figure checksums.
- Reference verification notes.
- Evidence paths and line references.
- Unresolved issues.

Use CSV for machine-readable claim and work-package ledgers where useful.

## 10. CLAIM DISPOSITIONS

Every important claim must receive exactly one status:

VERIFIED
CORRECT_BUT_REWORD
UNVERIFIED
INCORRECT

Every claim must include:
- Claim ID.
- Exact claim.
- Source document and location.
- Primary evidence.
- Verification method.
- Previous status.
- New status.
- Discrepancy.
- Required correction.
- Whether rerunning an experiment is necessary.
- Chief reviewer sign-off.

## 11. AGENT ACCOUNTABILITY

Maintain a live ledger.

Do not count:
- KILLED agents as completed.
- FAILED agents as completed.
- BLOCKED agents as completed.
- Duplicate work as independent work.
- An agent's self-review as independent sign-off.

If a quota limit or agent limit is reached:
1. Record the actual limit/error.
2. Save completed work.
3. Queue the remaining tasks.
4. Continue in sequential batches where possible.
5. Never silently abandon tasks.
6. Never report all 100 work packages complete unless all 100 have evidence-backed results.

Use the available Agent Manager to inspect actual agent status.

## 12. FINAL VERDICT

The chief auditor must choose one:

READY_FOR_PREPRINT
READY_AFTER_DOCUMENTATION_CORRECTIONS
READY_AFTER_REANALYSIS
NOT_READY

Explain every blocker.

Do not say only a Git push remains unless all scientific and documentation checks genuinely support that conclusion.

Do not push.

## 13. COMPLETION CONDITIONS

This audit is complete only when:
- Five master reports exist.
- All 100 work packages have a recorded disposition.
- Ten verification passes are documented for critical claims.
- Chief auditor has independently reviewed the findings.
- Previous reports are compared.
- Scientific validation is completed or explicitly blocked.
- All discrepancies are documented.
- Local outputs exist.
- No protected project files were modified.

If any task cannot be completed, mark it UNVERIFIED and explain why.

Truthful incompleteness is preferable to fabricated completion.
