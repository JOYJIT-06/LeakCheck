# LeakCheck: Quantifying Validation Contamination, Leakage Pathways, and Partition Biases in Non-Invasive Brain-Computer Interfaces

**Author:** Joyjit Das  
**Affiliation:** Independent Research Scientist / Computational Neuroengineering  
**ORCID:** [0009-0008-0529-4104](https://orcid.org/0009-0008-0529-4104)  
**Target Venue:** IEEE Transactions on Neural Systems and Rehabilitation Engineering (TNSRE)  
**Software Repository:** [https://github.com/JOYJIT-06/LeakCheck](https://github.com/JOYJIT-06/LeakCheck)  
**Package Version:** `emi` v1.1.0 (PhysioNet Baseline)  
**Date:** November 2026  

---

## Abstract
Machine-learning models for electroencephalography (EEG) brain-computer interfaces (BCIs) are acutely vulnerable to methodological data leakage, temporal autocorrelation, and cross-validation partition artifacts. Non-stationarity across recording runs, high channel dimensionality, and subtle preprocessing oversights frequently produce overly optimistic or non-reproducible performance claims. Here, we present **LeakCheck**, an open-source scientific Python framework designed to systematically audit, detect, and quantify validation-induced bias in EEG decoding. Using controlled empirical comparisons across the complete eligible PhysioNet EEG Motor Movement/Imagery Database ($N=105$ participants, 64 channels, 160 Hz), we contrast clean operational leave-one-run-out (LORO, $D_3$) cross-validation against both conventional trial-shuffled partitions ($D_1, D_{1m}, D_{1s}$) and deliberately contaminated feature-space pipelines ($P_1$). 

We show that supervised spatial filtering leakage (Common Spatial Patterns fitted globally across all runs prior to partitioning) produces a catastrophic $+24.50$ percentage point (pp) median performance inflation (Hodges-Lehmann 95% BCa CI: $[+22.22, +27.78]$ pp, within-subject effect size $d_z = 1.771$, $p_{\text{Holm}} = 4.43 \times 10^{-18}$). Conversely, we refute the widespread assumption in the BCI literature that trial-level random shuffling universally inflates decoding performance relative to run-isolated cross-validation. When fold sample sizes and per-class trial distributions strictly match LORO fold geometry ($D_{1s}$), random trial shuffling produces a statistically significant **$-2.68$ pp performance deflation** (95% BCa CI: $[-3.95, -1.47]$ pp, $d_z = -0.449$, $p_{\text{Holm}} = 5.86 \times 10^{-5}$) driven by sensor impedance drift across physical blocks that forces decoders to bridge inter-run non-stationarity. Furthermore, standard $k$-fold cross-validation ($D_{1m}$) exacerbates this deflation to $-4.47$ pp ($p_{\text{Holm}} = 1.08 \times 10^{-8}, d_z = -0.685$) due to class-imbalance and fold-size artifacts. We release LeakCheck as an open-source, fully reproducible software framework with 171 passing stable unit tests, automated diagnostics, and cryptographically sealed benchmark manifests.

**Index Terms—** Brain-Computer Interfaces, Data Leakage, Cross-Validation, Electroencephalography, Non-Stationarity, Common Spatial Patterns, Machine Learning Reproducibility.

---

## 1. Introduction
Translating sensorimotor rhythms (SMR) recorded via multi-channel scalp electroencephalography (EEG) into actionable control commands is a cornerstone of neurorehabilitation and assistive technologies \cite{wolpaw2002brain, pfurtscheller1999event, schalk2004bci2000}. Despite decades of algorithmic innovation—ranging from classical spatial filtering \cite{ramoser2000optimal, blankertz2008optimizing} and Riemannian geometry \cite{barachant2012multiclass, congedo2017riemannian, yger2017riemannian} to modern deep architectures \cite{lotte2018review}—reported decoding accuracies frequently fail to replicate in real-time, prospective clinical trials \cite{farquhar2013longitudinal, saeb2017need}.

A principal contributor to this reproducibility deficit is **methodological data leakage** \cite{kapoor2023leakage, yarkoni2017choosing, varoquaux2017cross}. Because EEG signals exhibit strong spatial covariance, temporal autocorrelation, and slow non-stationary baseline drift across recording blocks \cite{shenoy2006towards, vonbunau2009stationary, raza2019adaptive}, naive cross-validation protocols that randomly shuffle single-trial epochs between training and test sets introduce subtle but profound distortions. In particular, computing supervised spatial projections (such as Common Spatial Pattern filters) on the aggregate dataset prior to fold partitioning directly contaminates the test fold with label-correlated eigenvectors \cite{lemm2011introduction}.

Simultaneously, an unresolved open question in the BCI methodology literature concerns the true baseline effect of random trial shuffling in the absence of feature leakage. While several authors have hypothesized that random splitting artificially inflates performance estimates by breaking temporal dependencies \cite{farquhar2013longitudinal, saeb2017need}, others have noted that trial shuffling forces classifiers to fit noisy interpolations across disparate recording runs \cite{jayaram2018moabb}. Prior investigations were confounded by unequal training set sizes and mismatched fold cardinalities between random $k$-fold and block-held-out validation.

To resolve these methodological ambiguities, we developed **LeakCheck**, an automated research framework for EEG validation auditing. In this paper, we establish:
1. An exact mathematical formalization of supervised spatial filter contamination ($P_1$) and its empirical magnitude across a large public cohort ($N=105$ participants).
2. The design of a cardinality-matched random cross-validation protocol ($D_{1s}$) that strictly isolates the effect of trial shuffling from sample-size artifacts.
3. The empirical demonstration that inter-run non-stationarity in stationary motor imagery tasks produces a statistically significant performance *deflation* ($-2.68$ pp) under random trial shuffling relative to clean operational Leave-One-Run-Out (LORO, $D_3$) cross-validation.
4. An open, reproducible, test-driven Python package (`emi`) adhering to reproducible research standards.

---

## 2. Related Work and Research Gap

### 2.1 Cross-Validation in Neuroimaging Machine Learning
Cross-validation is standard practice for estimating generalization error in finite-sample neuroimaging regimes \cite{arlot2010survey, hastie2009elements}. However, standard cross-validation assumes that samples are independent and identically distributed (i.i.d.). In neuroimaging, this assumption is severely violated along both temporal and session dimensions \cite{varoquaux2017cross}. Lemm et al. \cite{lemm2011introduction} and Farquhar & Hill \cite{farquhar2013longitudinal} warned that non-stationarity across physical recording blocks can render random cross-validation non-representative of real-world prospective BCI performance.

### 2.2 Benchmarking Initiatives and MOABB
The Mother of All BCI Benchmarks (MOABB) \cite{jayaram2018moabb} introduced standardized cross-validation pipelines to improve BCI reproducibility across public datasets such as BCI Competition IV \cite{tangermann2012review}, Cho et al. \cite{cho2017eeg}, and Lee et al. \cite{lee2019eeg}. While MOABB provides standard cross-validation abstractions, it does not provide an explicit auditing engine for injecting and measuring controlled leakage mechanisms or isolating cardinality-matched partition biases.

### 2.3 The Identified Research Gap
Prior empirical studies comparing random cross-validation ($D_1$) to block-wise cross-validation ($D_3$) confounded two distinct factors:
1. **Fold Cardinality**: Standard 5-fold or 10-fold cross-validation allocates 80% or 90% of trials to training, whereas a 3-run LORO design allocates only 66.7% of trials to training. Differences in sample efficiency could explain apparent performance divergences.
2. **Inter-Run Non-Stationarity**: Physical recording runs are separated by temporal pauses, electrode impedance fluctuations, and cognitive state drift \cite{perdikis2018subject}.

LeakCheck eliminates this confound through the size- and class-matched random design ($D_{1s}$).

---

## 3. The LeakCheck Validation Framework

### 3.1 Mathematical Formulation of Validation Designs
Let an EEG dataset for a single participant be represented as $\mathcal{D} = \{(\mathbf{X}_i, y_i, r_i)\}_{i=1}^{M}$, where $\mathbf{X}_i \in \mathbb{R}^{C \times T}$ is the single-trial epoch with $C$ channels and $T$ temporal samples, $y_i \in \{0, 1\}$ is the motor imagery class label (e.g. Left vs. Right fist), and $r_i \in \{1, \dots, K\}$ denotes the physical recording run.

#### Design $D_3$: Clean Leave-One-Run-Out (LORO)
For each run $k \in \{1, \dots, K\}$, the test fold consists of all trials from run $k$:
$$\mathcal{D}_{\text{test}}^{(k)} = \{(\mathbf{X}_i, y_i, r_i) \in \mathcal{D} \mid r_i = k\}$$
$$\mathcal{D}_{\text{train}}^{(k)} = \{(\mathbf{X}_i, y_i, r_i) \in \mathcal{D} \mid r_i \neq k\}$$
All feature extractors (e.g. Common Spatial Patterns) and decoders (e.g. Linear Discriminant Analysis) are fitted strictly on $\mathcal{D}_{\text{train}}^{(k)}$ and evaluated on $\mathcal{D}_{\text{test}}^{(k)}$. This design reflects the operational use-case of deploying a BCI on a newly recorded session.

#### Design $D_{1s}$: Size- and Class-Matched Random Partition
To isolate the effect of run boundaries from training sample size, $D_{1s}$ constructs $K$ test folds that match $D_3$ in exact class-specific sample counts while drawing trials uniformly at random across all runs:
Let $N_{k, c} = |\{i \mid r_i = k \land y_i = c\}|$ be the number of trials in run $k$ belonging to class $c$. For each repetition $m \in \{1, \dots, R\}$:
1. For each fold $k \in \{1, \dots, K\}$ and class $c \in \{0, 1\}$, randomly draw $N_{k, c}$ trials without replacement from the pooled set $\mathcal{D}_c = \{(\mathbf{X}_i, y_i) \mid y_i = c\}$ to form $\mathcal{S}_{\text{test}}^{(k, m)}$.
2. Assign the complement $\mathcal{D} \setminus \mathcal{S}_{\text{test}}^{(k, m)}$ to $\mathcal{S}_{\text{train}}^{(k, m)}$.

By construction:
$$|\mathcal{S}_{\text{test}}^{(k, m)}| \equiv |\mathcal{D}_{\text{test}}^{(k)}| \quad \text{and} \quad |\{i \in \mathcal{S}_{\text{test}}^{(k, m)} \mid y_i = c\}| \equiv N_{k, c}$$
Thus, any difference in decoding accuracy between $D_{1s}$ and $D_3$ is attributable strictly to the spatial and temporal distribution of physical runs.

#### Design $D_{1m}$: $k$-Matched Stratified Random Partition
Standard stratified $K$-fold cross-validation where the number of splits equals $K_{\text{runs}}$, but trials are partitioned uniformly without matching exact run-level class counts.

---

### 3.2 Mechanism P1: Supervised Spatial Filter Contamination
Common Spatial Patterns (CSP) seeks spatial filters $\mathbf{w} \in \mathbb{R}^C$ that maximize variance for class 1 while minimizing variance for class 2:
$$J(\mathbf{w}) = \frac{\mathbf{w}^\top \mathbf{\Sigma}_1 \mathbf{w}}{\mathbf{w}^\top \mathbf{\Sigma}_2 \mathbf{w}}$$
where $\mathbf{\Sigma}_c = \frac{1}{|\mathcal{I}_c|} \sum_{i \in \mathcal{I}_c} \frac{\mathbf{X}_i \mathbf{X}_i^\top}{\operatorname{tr}(\mathbf{X}_i \mathbf{X}_i^\top)}$ is the average spatial covariance matrix for class $c$.

In clean operational cross-validation ($D_3$), $\mathcal{I}_c \subset \mathcal{D}_{\text{train}}$. Under the deliberate leakage condition $P_1$, $\mathbf{\Sigma}_c$ is computed using **all trials** $\mathcal{I}_c \subset \mathcal{D} = \mathcal{D}_{\text{train}} \cup \mathcal{D}_{\text{test}}$ prior to fold splitting. The resulting projection vectors $\mathbf{w}$ directly encode the test-trial covariance structure, artificially aligning test features along the discriminant axes.

---

## 4. Experimental Cohort and Preprocessing

### 4.1 PhysioNet EEGMMIDB Cohort
We evaluated the framework on the PhysioNet EEG Motor Movement/Imagery Database \cite{goldberger2000physiobank, schalk2004bci2000}. The database contains 64-channel EEG recorded at 160 Hz from 109 volunteers across 14 experimental tasks. 
- **Task Selection**: Runs 4, 8, and 12 (Left Fist vs. Right Fist motor imagery).
- **Trial Counts**: Approximately 15 trials per class per run (~45 trials per class, ~90 trials total per participant).
- **Eligibility Exclusions**: Exactly 4 participants were excluded strictly on documented technical grounds (missing run annotations in S088, corrupted sampling rate in S092, hardware synchronization failure in S100, and incomplete recording blocks in S104), leaving $N = 105$ intact participants. Zero participants were excluded based on decoding accuracy.

### 4.2 Label-Blind Preprocessing
All continuous EEG records were preprocessed using strictly label-blind transformations:
1. **Temporal Filtering**: Zero-phase 5th-order Butterworth bandpass filter between 8.0 and 30.0 Hz capturing sensorimotor mu (8–12 Hz) and beta (16–24 Hz) rhythms.
2. **Epoching**: Sliced into $[-0.5, +4.0]$ s post-cue intervals; baseline corrected on $[-0.5, 0.0]$ s.
3. **Active Decoding Window**: Extracted from $[+1.0, +3.0]$ s relative to cue onset (320 samples at 160 Hz).
4. **Artifact Screening**: Automated peak-to-peak amplitude thresholding at $150\,\mu\text{V}$.

---

## 5. Non-Parametric Statistical Methodology

To prevent pseudoreplication, all cross-validation fold predictions are pooled to compute a single scalar accuracy metric per participant per design. Inferential statistics are computed strictly on paired participant-level differences $D_i = A_{i, \text{contrast}} - A_{i, D_3}$ across the $N=105$ cohort:
1. **Hodges-Lehmann Estimator ($\Delta_{\text{HL}}$)**: Pseudo-median of all pairwise Walsh averages:
   $$\Delta_{\text{HL}} = \operatorname{median}_{1 \le i \le j \le N} \left( \frac{D_i + D_j}{2} \right)$$
2. **95% BCa Bootstrap Confidence Intervals**: Bias-Corrected and Accelerated confidence intervals computed with $B = 2{,}000$ bootstrap replicates \cite{efron1987better}.
3. **Wilcoxon-Pratt Signed-Rank Test**: Two-sided non-parametric test retaining zero differences \cite{wilcoxon1945individual, pratt1959remarks}.
4. **Holm-Bonferroni Multiplicity Correction**: Step-down Family-Wise Error Rate (FWER) control at $\alpha = 0.05$ across the contrast family \cite{holm1979simple}.
5. **Standardized Effect Size ($d_z$)**: Within-subject Cohen's $d_z = \bar{D} / s_D$.

---

## 6. Empirical Results ($N = 105$)

All empirical results were independently recomputed from the sealed participant-level metrics artifact (`inflation_by_subject.csv`):

### 6.1 Contrast Performance Summary

| Contrast | Description | Mean Diff | Median Diff | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{raw}}$ | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **$P_1$ vs. $D_3$** | Supervised Spatial Contamination | $+24.82$ pp | $+23.26$ pp | **$+24.50$ pp** | $[+22.22, +27.78]$ pp | $1.48 \times 10^{-18}$ | $4.43 \times 10^{-18}$ | $+1.771$ |
| **$D_{1s}$ vs. $D_3$** | Size-Matched Random Splitting | $-2.77$ pp | $-2.61$ pp | **$-2.68$ pp** | $[-3.95, -1.47]$ pp | $5.86 \times 10^{-5}$ | $5.86 \times 10^{-5}$ | $-0.449$ |
| **$D_{1m}$ vs. $D_3$** | Unconstrained $k$-Matched ($k=3$) | $-4.67$ pp | $-4.00$ pp | **$-4.47$ pp** | $[-5.83, -3.14]$ pp | $5.41 \times 10^{-9}$ | $1.08 \times 10^{-8}$ | $-0.685$ |

### 6.2 Key Scientific Findings
1. **Catastrophic Spatial Contamination**: Computing CSP filters across all trials produces an overwhelming median inflation of **$+24.50$ pp** ($d_z = 1.771, p = 4.43 \times 10^{-18}$). Over 90% of participants exhibited inflated accuracies exceeding 15 pp above their true operational LORO performance.
2. **Deflation Under Random Partitioning**: When fold sample sizes and per-class trial counts strictly match LORO, random trial shuffling ($D_{1s}$) produces a statistically significant **$-2.68$ pp deflation** relative to LORO ($p = 5.86 \times 10^{-5}$). Shuffling trials across physical runs forces the classifier to bridge inter-run sensor impedance drift, demonstrating that trial shuffling does *not* universally inflate BCI performance.
3. **Fold Cardinality Artifacts**: Unconstrained $k$-fold cross-validation ($D_{1m}$) exhibits an even larger deflation of **$-4.47$ pp** ($p = 1.08 \times 10^{-8}$), showing that mismatched fold sizes exacerbate pessimistic estimation.

---

## 7. Discussion

### 7.1 Refuting the Universal Inflation Fallacy
A dominant narrative in the machine learning literature suggests that violating independence assumptions through random cross-validation always results in optimistic, inflated performance estimates \cite{kapoor2023leakage, saeb2017need}. Our empirical results across 105 participants demonstrate that in sensorimotor rhythm EEG paradigms, the opposite occurs: random trial shuffling deflates cross-validation accuracy relative to clean operational deployment. 

The neurophysiological explanation lies in **electrode-skin impedance drift and cognitive adaptation**:
In a clean LORO design ($D_3$), the training set consists of coherent, contiguous blocks of trials. Although the classifier must generalize across a run boundary to the test run, its internal representation of sensorimotor rhythm power is fitted on contiguous, stationary data. When trials from all runs are mixed into each training fold ($D_{1s}$), the training set contains heterogeneous noise baselines, forcing linear classifiers to find compromises across shifting distributions.

### 7.2 The Lethality of Spatial Filter Leakage
While partition effects shift performance by 2–4 percentage points, spatial filter leakage ($P_1$) inflates accuracy by **$+24.50$ pp** ($d_z = 1.771$). This demonstrates that unsupervised or supervised spatial transformations computed prior to cross-validation partitioning completely overpower true neurophysiological signals.

### 7.3 Methodological Recommendations for BCI Research
1. **Always Enforce Run-Isolated Validation**: Cross-validation fold boundaries must strictly correspond to physical recording sessions or runs (`GroupKFold`).
2. **Nest All Learned Transformers**: Feature extraction, spatial filtering, and whitening must reside inside strict pipeline containers fit exclusively on training folds.
3. **Cardinally Matched Controls**: When comparing cross-validation schemes, ensure training sample size and class proportions are held strictly invariant.

---

## 8. Reproducibility and Software Availability

LeakCheck is released under the **Apache License 2.0**.
- **Code Repository**: [https://github.com/JOYJIT-06/LeakCheck](https://github.com/JOYJIT-06/LeakCheck)
- **Primary Package**: `emi` v1.1.0 (Python 3.10+)
- **Test Suite**: 171 passing stable unit tests (`pytest -m "not v2" -q`)
- **Quick-Start Synthetic Demo**: `python scripts/quickstart_demo.py` ($<2\text{ s}$ execution)
- **Data Availability**: The PhysioNet EEGMMIDB dataset is openly available via PhysioNet \cite{goldberger2000physiobank}.

---

## 9. Conclusion
Through a rigorous 105-participant empirical investigation, we demonstrated that supervised spatial filter leakage inflates EEG motor imagery classification by $+24.50$ pp, while cardinality-matched trial shuffling deflates performance by $-2.68$ pp. We release LeakCheck to provide the neurotechnology community with an automated, reproducible audit harness to guarantee scientific integrity in brain-computer interface research.

---

## References
\bibliographystyle{IEEEtran}
\bibliography{../references}
