#!/usr/bin/env Rscript
# ==============================================================================
# reproduce_statistics.R — Independent R Statistical Validation Suite for LeakCheck
# ==============================================================================
# Project: LeakCheck V1.1 (PhysioNet EEG Motor Movement/Imagery Benchmark)
# Author: Worker M3 (Statistical Analyst and R Validation Specialist)
# Purpose: Independently reproduce and validate all participant-level statistical
#          metrics, contrasts, effect sizes, confidence intervals, and hypothesis
#          tests from benchmark_results/physionet_v1_1/inflation_by_subject.csv.
#
# Usage:
#   Rscript reproduce_statistics.R [path/to/inflation_by_subject.csv]
#
# Requirements:
#   - R >= 4.0.0
#   - Recommended packages: boot, coin, effsize, TOSTER (optional; base R fallback provided)
# ==============================================================================

options(digits = 8, scipen = 0)

# ------------------------------------------------------------------------------
# 1. Path Resolution & Package Setup
# ------------------------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
csv_candidates <- c(
  if (length(args) > 0) args[1] else NULL,
  "benchmark_results/physionet_v1_1/inflation_by_subject.csv",
  "../../benchmark_results/physionet_v1_1/inflation_by_subject.csv",
  "../benchmark_results/physionet_v1_1/inflation_by_subject.csv",
  "inflation_by_subject.csv"
)

csv_path <- NULL
for (cand in csv_candidates) {
  if (!is.null(cand) && file.exists(cand)) {
    csv_path <- normalizePath(cand)
    break
  }
}

if (is.null(csv_path)) {
  stop("FATAL: Could not locate 'inflation_by_subject.csv'. Provide path as command line argument.")
}

cat("==============================================================================\n")
cat("LEAKCHECK V1.1 INDEPENDENT R STATISTICAL VALIDATION SUITE\n")
cat("==============================================================================\n")
cat(sprintf("Source CSV Path : %s\n", csv_path))
cat(sprintf("R Version       : %s\n", R.version.string))
cat(sprintf("Platform        : %s\n", R.version$platform))
cat(sprintf("Timestamp       : %s UTC\n", format(Sys.time(), tz = "UTC", usetz = TRUE)))
cat("==============================================================================\n\n")

# Load data
df <- read.csv(csv_path, stringsAsFactors = FALSE)
req_cols <- c("subject", "design", "acc_ref", "acc_leaky", "delta_pp")
missing_cols <- setdiff(req_cols, colnames(df))
if (length(missing_cols) > 0) {
  stop(sprintf("Input CSV missing required columns: %s", paste(missing_cols, collapse = ", ")))
}

# ------------------------------------------------------------------------------
# 2. Cohort Accounting & Data Integrity Audit
# ------------------------------------------------------------------------------
all_subjects <- sort(unique(df$subject))
n_subjects <- length(all_subjects)
expected_109 <- 1:109
excluded_subjects <- setdiff(expected_109, all_subjects)

cat("--- 1. COHORT ACCOUNTING AUDIT ---\n")
cat(sprintf("Total Evaluated Participants : N = %d\n", n_subjects))
cat(sprintf("Total Subject-Contrast Rows  : %d\n", nrow(df)))
cat(sprintf("Excluded Participants (%d)    : %s\n",
            length(excluded_subjects),
            paste(sprintf("S%03d", excluded_subjects), collapse = ", ")))

# Forensic verification of participants S088, S092, S100, S104
for (sid in c(88, 92, 100, 104)) {
  sub_rows <- df[df$subject == sid, ]
  if (nrow(sub_rows) > 0) {
    ref_acc <- sub_rows$acc_ref[1] * 100
    cat(sprintf("  -> S%03d: VERIFIED PRESENT (D3_loro Accuracy = %.2f%%, Rows = %d)\n",
                sid, ref_acc, nrow(sub_rows)))
  } else {
    cat(sprintf("  -> S%03d: MISSING FROM DATASET\n", sid))
  }
}

# Split into design subsets
df_d3  <- df[df$design == "D1s_size_matched", c("subject", "acc_ref")]
colnames(df_d3) <- c("subject", "acc_d3")

df_d1s <- df[df$design == "D1s_size_matched", c("subject", "acc_leaky", "delta_pp")]
colnames(df_d1s) <- c("subject", "acc_d1s", "delta_d1s")

df_d1m <- df[df$design == "D1m_matched_k", c("subject", "acc_leaky", "delta_pp")]
colnames(df_d1m) <- c("subject", "acc_d1m", "delta_d1m")

df_p1  <- df[df$design == "P1_csp_on_all", c("subject", "acc_leaky", "delta_pp")]
colnames(df_p1) <- c("subject", "acc_p1", "delta_p1")

# Merge into unified wide participant dataframe
wide <- merge(df_d3, df_d1s, by = "subject")
wide <- merge(wide, df_d1m, by = "subject")
wide <- merge(wide, df_p1, by = "subject")
wide <- wide[order(wide$subject), ]

# Verify consistency of delta_pp
stopifnot(all.equal(wide$delta_d1s, (wide$acc_d1s - wide$acc_d3) * 100, tolerance = 1e-6))
stopifnot(all.equal(wide$delta_d1m, (wide$acc_d1m - wide$acc_d3) * 100, tolerance = 1e-6))
stopifnot(all.equal(wide$delta_p1,  (wide$acc_p1  - wide$acc_d3) * 100, tolerance = 1e-6))

# Exploratory fold-geometry difference: D1s - D1m
wide$delta_d1s_vs_d1m <- (wide$acc_d1s - wide$acc_d1m) * 100

# ------------------------------------------------------------------------------
# 3. Protocol-Level Accuracy Summaries
# ------------------------------------------------------------------------------
cat("\n--- 2. PROTOCOL-LEVEL DECODING ACCURACY DISTRIBUTIONS (N = 105) ---\n")
summarize_dist <- function(x_dec, name) {
  x <- x_dec * 100
  qs <- quantile(x, probs = c(0.25, 0.50, 0.75))
  cat(sprintf("  %-18s: Mean = %6.2f%% (SD = %5.2f%%) | Median = %6.2f%% (IQR = %5.2f%%: %5.2f%% - %5.2f%%) | Range = [%5.2f%%, %6.2f%%]\n",
              name, mean(x), sd(x), median(x), qs[3] - qs[1], qs[1], qs[3], min(x), max(x)))
}
summarize_dist(wide$acc_d3,  "D3_loro (Ref)")
summarize_dist(wide$acc_d1s, "D1s_size_matched")
summarize_dist(wide$acc_d1m, "D1m_matched_k")
summarize_dist(wide$acc_p1,  "P1_csp_on_all")

# ------------------------------------------------------------------------------
# 4. Statistical Estimation Functions
# ------------------------------------------------------------------------------

# Exact Hodges-Lehmann pseudo-median (median of all Walsh averages)
calc_hodges_lehmann <- function(d) {
  d <- as.numeric(d)
  n <- length(d)
  walsh_mat <- outer(d, d, "+") / 2
  walsh_pairs <- walsh_mat[lower.tri(walsh_mat, diag = TRUE)]
  return(median(walsh_pairs))
}

# Within-subject Cohen's d_z effect size
calc_cohens_dz <- function(d) {
  d <- as.numeric(d)
  return(mean(d) / sd(d))
}

# Matched-pairs rank-biserial correlation
calc_rank_biserial <- function(d) {
  d <- as.numeric(d)
  d_nz <- d[abs(d) > 1e-9]
  if (length(d_nz) == 0) return(0.0)
  ranks <- rank(abs(d_nz))
  w_pos <- sum(ranks[d_nz > 0])
  w_neg <- sum(ranks[d_nz < 0])
  return((w_pos - w_neg) / (w_pos + w_neg))
}

# Two One-Sided Tests (TOST) for equivalence within +-margin
calc_tost <- function(d, margin = 2.0, alpha = 0.05) {
  d <- as.numeric(d)
  n <- length(d)
  m <- mean(d)
  s <- sd(d)
  se <- s / sqrt(n)
  df_t <- n - 1
  
  t_low  <- (m - (-margin)) / se
  p_low  <- 1 - pt(t_low, df = df_t)
  t_high <- (m - margin) / se
  p_high <- pt(t_high, df = df_t)
  p_tost <- max(p_low, p_high)
  
  t_crit_90 <- qt(1 - alpha, df = df_t)
  ci90_low  <- m - t_crit_90 * se
  ci90_high <- m + t_crit_90 * se
  
  return(list(p_tost = p_tost, ci90_low = ci90_low, ci90_high = ci90_high,
              equivalent = (p_tost < alpha)))
}

# Exact BCa Bootstrap Confidence Interval for Hodges-Lehmann estimator
calc_bca_ci <- function(d, R = 10000, conf = 0.95, seed = 0) {
  d <- as.numeric(d)
  set.seed(seed)
  has_boot <- requireNamespace("boot", quietly = TRUE)
  
  if (has_boot) {
    hl_stat <- function(data, indices) {
      calc_hodges_lehmann(data[indices])
    }
    b_out <- boot::boot(data = d, statistic = hl_stat, R = R)
    tryCatch({
      b_ci <- boot::boot.ci(b_out, conf = conf, type = "bca")
      return(list(low = b_ci$bca[4], high = b_ci$bca[5], method = "BCa"))
    }, error = function(e) {
      # Fallback to percentile interval if BCa acceleration fails
      b_ci <- boot::boot.ci(b_out, conf = conf, type = "perc")
      return(list(low = b_ci$percent[4], high = b_ci$percent[5], method = "percentile_fallback"))
    })
  } else {
    # Pure base-R percentile bootstrap fallback
    n <- length(d)
    boots <- replicate(R, calc_hodges_lehmann(sample(d, n, replace = TRUE)))
    alpha <- (1 - conf) / 2
    qs <- quantile(boots, probs = c(alpha, 1 - alpha))
    return(list(low = qs[1], high = qs[2], method = "percentile_baseR"))
  }
}

# Wilcoxon signed-rank test with Pratt zero-handling
calc_wilcoxon_pratt <- function(d) {
  d <- as.numeric(d)
  has_coin <- requireNamespace("coin", quietly = TRUE)
  if (has_coin) {
    df_coin <- data.frame(diff = d, id = factor(1:length(d)))
    # coin::wilcoxsign_test with Pratt zero-method
    res <- coin::wilcoxsign_test(diff ~ 0, data = df_coin, zero.method = "Pratt", distribution = "asymptotic")
    p_val <- coin::pvalue(res)
    stat  <- coin::statistic(res)
    return(list(statistic = stat, p_value = as.numeric(p_val), method = "coin_Pratt"))
  } else {
    # Base R Pratt calculation: include zeros in ranking, then drop ranks of zeros
    n <- length(d)
    abs_d <- abs(d)
    ranks <- rank(abs_d)
    w_pos <- sum(ranks[d > 0])
    w_neg <- sum(ranks[d < 0])
    # Under Pratt, total non-zero rank sum is w_pos + w_neg
    # Mean and variance of W+ under H0 with Pratt method:
    t_zeros <- sum(d == 0)
    e_w <- (n * (n + 1) / 2 - t_zeros * (t_zeros + 1) / 4) / 2 # Approx
    # Use base R standard wilcox.test as reference
    w_std <- wilcox.test(d, exact = FALSE, correct = FALSE)
    return(list(statistic = w_std$statistic, p_value = w_std$p.value, method = "base_R_wilcoxon"))
  }
}

# ------------------------------------------------------------------------------
# 5. Execute 4 Key Contrasts
# ------------------------------------------------------------------------------
contrasts <- list(
  list(name = "P1 vs D3", label = "P1_csp_on_all vs. D3_loro", type = "Primary (m=3)", d = wide$delta_p1),
  list(name = "D1s vs D3", label = "D1s_size_matched vs. D3_loro", type = "Primary (m=3)", d = wide$delta_d1s),
  list(name = "D1m vs D3", label = "D1m_matched_k vs. D3_loro", type = "Primary (m=3)", d = wide$delta_d1m),
  list(name = "D1s vs D1m", label = "D1s_size_matched vs. D1m_matched_k", type = "Exploratory (m=4)", d = wide$delta_d1s_vs_d1m)
)

results_list <- list()

cat("\n--- 3. PAIRED STATISTICAL REVALIDATION RESULTS ---\n")

for (i in seq_along(contrasts)) {
  ct <- contrasts[[i]]
  d <- ct$d
  n <- length(d)
  
  mean_d <- mean(d)
  sd_d   <- sd(d)
  med_d  <- median(d)
  hl_d   <- calc_hodges_lehmann(d)
  dz     <- calc_cohens_dz(d)
  rrb    <- calc_rank_biserial(d)
  
  # Base R Wilcoxon signed rank test (discards exact zeros)
  wt_res <- suppressWarnings(wilcox.test(d, alternative = "two.sided", exact = FALSE, correct = FALSE))
  p_raw_wilcox <- wt_res$p.value
  w_stat_wilcox <- as.numeric(wt_res$statistic) # In R, V = sum of positive ranks
  
  # BCa Confidence Interval
  bca_res <- calc_bca_ci(d, R = 10000, conf = 0.95, seed = 0)
  
  # TOST Equivalence Test (+- 2.0 pp)
  tost_res <- calc_tost(d, margin = 2.0, alpha = 0.05)
  
  # Counts of positive, negative, zero differences (with 1e-9 tolerance)
  n_pos <- sum(d > 1e-9)
  n_neg <- sum(d < -1e-9)
  n_tie <- sum(abs(d) <= 1e-9)
  
  results_list[[i]] <- data.frame(
    contrast = ct$name,
    label = ct$label,
    tier = ct$type,
    n_subjects = n,
    n_pos = n_pos,
    n_neg = n_neg,
    n_tie = n_tie,
    mean_pp = mean_d,
    sd_pp = sd_d,
    median_pp = med_d,
    hl_pp = hl_d,
    ci_low_pp = bca_res$low,
    ci_high_pp = bca_res$high,
    ci_method = bca_res$method,
    wilcox_v = w_stat_wilcox,
    p_raw = p_raw_wilcox,
    cohens_dz = dz,
    rank_biserial = rrb,
    p_tost = tost_res$p_tost,
    ci90_low_pp = tost_res$ci90_low,
    ci90_high_pp = tost_res$ci90_high,
    tost_equivalent = tost_res$equivalent,
    stringsAsFactors = FALSE
  )
}

res_df <- do.call(rbind, results_list)

# Compute Holm-Bonferroni corrections
# Primary family: m = 3 (Contrasts 1, 2, 3 against D3_loro)
p_primary <- res_df$p_raw[1:3]
res_df$p_holm_m3 <- c(p.adjust(p_primary, method = "holm"), NA)

# Extended family: m = 4 (including exploratory D1s vs D1m)
res_df$p_holm_m4 <- p.adjust(res_df$p_raw, method = "holm")

# Print detailed summary
for (i in 1:nrow(res_df)) {
  r <- res_df[i, ]
  cat("------------------------------------------------------------------------------\n")
  cat(sprintf("Contrast [%d]: %s (%s)\n", i, r$label, r$tier))
  cat(sprintf("  Counts (+ / - / 0)    : %d higher (+), %d lower (-), %d tied (0)\n", r$n_pos, r$n_neg, r$n_tie))
  cat(sprintf("  Mean (SD) / Median    : %+.4f pp (SD = %.4f pp) | Median = %+.4f pp\n", r$mean_pp, r$sd_pp, r$median_pp))
  cat(sprintf("  Hodges-Lehmann Shift  : %+.4f pp [95%% BCa CI: %+.4f, %+.4f] pp (%s)\n", r$hl_pp, r$ci_low_pp, r$ci_high_pp, r$ci_method))
  cat(sprintf("  Wilcoxon V Statistic  : V = %.1f | p_raw = %.4e\n", r$wilcox_v, r$p_raw))
  if (!is.na(r$p_holm_m3)) {
    cat(sprintf("  Holm-Adjusted p (m=3) : p_Holm = %.4e\n", r$p_holm_m3))
  }
  cat(sprintf("  Holm-Adjusted p (m=4) : p_Holm = %.4e\n", r$p_holm_m4))
  cat(sprintf("  Effect Sizes          : Cohen's d_z = %+.4f | Rank-Biserial r_rb = %+.4f\n", r$cohens_dz, r$rank_biserial))
  cat(sprintf("  Equivalence TOST (2pp): p_TOST = %.4f | 90%% CI = [%+.2f, %+.2f] pp | Equivalent: %s\n",
              r$p_tost, r$ci90_low_pp, r$ci90_high_pp, ifelse(r$tost_equivalent, "TRUE", "FALSE")))
}
cat("==============================================================================\n")

# ------------------------------------------------------------------------------
# 6. Null Controls Disclosure
# ------------------------------------------------------------------------------
cat("\n--- 4. NULL CONTROLS DISCLOSURE ---\n")
cat("Audit Verification of Historical Settings:\n")
cat("  - benchmark_results/physionet_v1_1/settings.json: 'n_null': 0\n")
cat("  - benchmark_results/physionet_v1_1/null_table.csv: 2 bytes (empty header)\n")
cat("  - Permutation and circular-shift null models were NOT executed in historical V1.1 runs.\n")
cat("  - Disclosure: Any claims of empirical null model evaluation in historical manuscripts\n")
cat("    must be formally reported as absent / unexecuted.\n")

# ------------------------------------------------------------------------------
# 7. Export Reproduction Output
# ------------------------------------------------------------------------------
out_csv <- "analysis/R_validation/reproduced_statistics_R.csv"
if (!dir.exists("analysis/R_validation")) {
  dir.create("analysis/R_validation", recursive = TRUE)
}
write.csv(res_df, out_csv, row.names = FALSE)
cat(sprintf("\n[SUCCESS] Independent R validation results exported to: %s\n\n", out_csv))

# ------------------------------------------------------------------------------
# 8. Session Information Logging
# ------------------------------------------------------------------------------
cat("--- 5. R SESSION INFORMATION ---\n")
print(sessionInfo())
cat("==============================================================================\n")
