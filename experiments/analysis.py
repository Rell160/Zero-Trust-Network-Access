"""
Statistical analysis & visualization generator for experimental research results.

Reads raw CSV experiment results and computes:
  - Mean & Standard Deviation
  - 95% Confidence Intervals (CI)
  - Normality Test (Shapiro-Wilk)
  - Hypothesis Significance Testing (Mann-Whitney U or Student's t-test)
  - 10 Key Variables Summary
  - Matplotlib High-Publication Quality Comparative Charts
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def analyze_and_plot_results(csv_path: str | Path, output_dir: str = "experiments/results") -> dict:
    """Perform statistical analysis on CSV benchmark data and produce paper plots.

    Args:
        csv_path: Path to the raw CSV results file.
        output_dir: Directory where plots and summary JSON/tables will be saved.

    Returns:
        Summary statistics dictionary.
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV results file not found: {csv_file}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} experiment records from {csv_file.name}")

    # Configurations: baseline_vpn, static_mfa, proposed_risk_aware
    configs = df["config_name"].unique()
    summary_metrics = {}

    for config in configs:
        sub = df[df["config_name"] == config]
        n = len(sub)

        # 1. Latencies
        auth_lat_mean = sub["auth_latency_ms"].mean()
        auth_lat_std = sub["auth_latency_ms"].std()

        pdp_lat_mean = sub["pdp_latency_ms"].mean()
        pdp_lat_std = sub["pdp_latency_ms"].std()

        mfa_resp_mean = sub["mfa_response_time_ms"].mean()

        # 2. Accuracy & Error Rates
        accuracy = sub["is_correct_decision"].mean() * 100.0

        # Malicious subset
        malicious_sub = sub[sub["is_malicious"] == True]
        total_attacks = len(malicious_sub)
        far = (malicious_sub["false_negative"].sum() / total_attacks) * 100.0 if total_attacks > 0 else 0.0
        prevention_rate = 100.0 - far

        # Legitimate subset
        legit_sub = sub[sub["is_malicious"] == False]
        total_legit = len(legit_sub)
        frr = (legit_sub["false_positive"].sum() / total_legit) * 100.0 if total_legit > 0 else 0.0

        # 3. Adaptation time
        adapt_mean = sub["adaptation_time_ms"].mean()

        # 4. CPU/RAM Utilization
        cpu_mean = sub["cpu_percent"].mean()
        ram_mean = sub["ram_mb"].mean()

        # 95% Confidence Interval for PDP Latency
        ci_95 = stats.sem(sub["pdp_latency_ms"]) * stats.t.ppf((1 + 0.95) / 2.0, n - 1)

        summary_metrics[config] = {
            "sample_size": n,
            "auth_latency_mean_ms": round(auth_lat_mean, 3),
            "auth_latency_std_ms": round(auth_lat_std, 3),
            "pdp_latency_mean_ms": round(pdp_lat_mean, 3),
            "pdp_latency_std_ms": round(pdp_lat_std, 3),
            "pdp_latency_ci95": round(ci_95, 3),
            "mfa_response_time_mean_ms": round(mfa_resp_mean, 3),
            "accuracy_percent": round(accuracy, 2),
            "far_percent": round(far, 2),
            "frr_percent": round(frr, 2),
            "unauthorized_prevention_rate_percent": round(prevention_rate, 2),
            "adaptation_time_mean_ms": round(adapt_mean, 3),
            "cpu_utilization_mean_percent": round(cpu_mean, 2),
            "ram_utilization_mean_mb": round(ram_mean, 2),
        }

    # Statistical Significance Testing (Proposed vs Static MFA on Latency & Accuracy)
    proposed_lat = df[df["config_name"] == "proposed_risk_aware"]["pdp_latency_ms"]
    static_lat = df[df["config_name"] == "static_mfa"]["pdp_latency_ms"]

    # Normality test
    _, shapiro_p = stats.shapiro(proposed_lat.sample(min(500, len(proposed_lat))))
    is_normal = shapiro_p > 0.05

    if is_normal:
        stat, p_val = stats.ttest_ind(proposed_lat, static_lat)
        test_used = "Student's t-test"
    else:
        stat, p_val = stats.mannwhitneyu(proposed_lat, static_lat)
        test_used = "Mann-Whitney U test"

    sig_summary = {
        "normality_p_value": round(shapiro_p, 5),
        "test_used": test_used,
        "statistic": round(stat, 3),
        "p_value": p_val,
        "is_statistically_significant": p_val < 0.05,
    }

    # Print Summary Table
    print("\n" + "=" * 70)
    print("      EXPERIMENTAL RESEARCH RESULTS & STATISTICAL SUMMARY")
    print("=" * 70)
    summary_df = pd.DataFrame(summary_metrics).T
    print(summary_df.to_string())
    print("\nSignificance Test (Latency: Proposed vs Static MFA):")
    print(f"  Test Used: {test_used}, Statistic: {stat:.3f}, p-value: {p_val:.5e}")
    print("=" * 70 + "\n")

    timestamp = csv_file.stem.replace("raw_benchmark_30rep_3config_", "")

    # Save Markdown Summary Table
    summary_md_path = out_dir / f"statistical_summary_10vars_3config_{timestamp}.md"
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# Summary of Experimental Measurements\n\n")
        f.write(summary_df.to_markdown() + "\n\n")
        f.write("## Hypothesis Testing\n\n")
        f.write(f"- **Test Executed**: {test_used}\n")
        f.write(f"- **Statistic**: {stat:.3f}\n")
        f.write(f"- **p-value**: {p_val:.5e}\n")
        f.write(f"- **Significant (p < 0.05)**: {p_val < 0.05}\n")

    # Also save as latest without timestamp
    latest_md_path = out_dir / "statistical_summary_10vars_3config.md"
    with open(latest_md_path, "w", encoding="utf-8") as f:
        f.write(summary_md_path.read_text(encoding="utf-8"))

    # Generate Publication Quality Plot
    generate_comparison_plots(df, out_dir, timestamp)

    return {"summary": summary_metrics, "significance": sig_summary}


def generate_comparison_plots(df: pd.DataFrame, out_dir: Path, timestamp: str = "") -> None:
    """Generate publication-ready comparison bar graphs."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    config_labels = {
        "baseline_vpn": "Baseline VPN",
        "static_mfa": "Static MFA",
        "proposed_risk_aware": "Proposed ZTNA",
    }
    colors = ["#7293CB", "#E1974C", "#84BA5B"]

    grouped = df.groupby("config_name")

    # Plot 1: Policy Decision Latency (ms) with Error Bars
    ax1 = axes[0, 0]
    lat_means = grouped["pdp_latency_ms"].mean()
    lat_sems = grouped["pdp_latency_ms"].sem() * 1.96  # 95% CI
    keys = list(config_labels.keys())
    x = np.arange(len(keys))
    ax1.bar(x, [lat_means[k] for k in keys], yerr=[lat_sems[k] for k in keys], capsize=5, color=colors)
    ax1.set_xticks(x)
    ax1.set_xticklabels([config_labels[k] for k in keys])
    ax1.set_ylabel("Latency (ms)")
    ax1.set_title("(a) Policy Decision Latency (95% CI)")

    # Plot 2: Access Control Accuracy (%)
    ax2 = axes[0, 1]
    acc_means = grouped["is_correct_decision"].mean() * 100.0
    ax2.bar(x, [acc_means[k] for k in keys], color=colors)
    ax2.set_xticks(x)
    ax2.set_xticklabels([config_labels[k] for k in keys])
    ax2.set_ylabel("Accuracy (%)")
    ax2.set_ylim(0, 105)
    ax2.set_title("(b) Access Control Decision Accuracy")

    # Plot 3: FAR vs FRR (%)
    ax3 = axes[1, 0]
    mal_df = df[df["is_malicious"] == True]
    leg_df = df[df["is_malicious"] == False]

    far_vals = [ (mal_df[mal_df["config_name"]==k]["false_negative"].sum() / len(mal_df[mal_df["config_name"]==k])) * 100 for k in keys]
    frr_vals = [ (leg_df[leg_df["config_name"]==k]["false_positive"].sum() / len(leg_df[leg_df["config_name"]==k])) * 100 for k in keys]

    width = 0.35
    ax3.bar(x - width/2, far_vals, width, label="FAR (False Accept)", color="#D62728")
    ax3.bar(x + width/2, frr_vals, width, label="FRR (False Reject)", color="#1F77B4")
    ax3.set_xticks(x)
    ax3.set_xticklabels([config_labels[k] for k in keys])
    ax3.set_ylabel("Error Rate (%)")
    ax3.set_title("(c) Security Error Rates (FAR vs FRR)")
    ax3.legend()

    # Plot 4: Mean MFA Response Overhead (ms)
    ax4 = axes[1, 1]
    mfa_means = grouped["mfa_response_time_ms"].mean()
    ax4.bar(x, [mfa_means[k] for k in keys], color=colors)
    ax4.set_xticks(x)
    ax4.set_xticklabels([config_labels[k] for k in keys])
    ax4.set_ylabel("Time (ms)")
    ax4.set_title("(d) Average User MFA Response Overhead")

    plt.tight_layout()
    if timestamp:
        plot_path = out_dir / f"comparative_evaluation_plots_30rep_{timestamp}.png"
        plt.savefig(plot_path, dpi=300)
    plot_path_latest = out_dir / "comparative_evaluation_plots_30rep.png"
    plt.savefig(plot_path_latest, dpi=300)
    plt.close()
    print(f"High-resolution comparative plots saved to: {plot_path_latest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze ZTNA Experiment CSV Results")
    parser.add_argument("--csv", type=str, required=True, help="Path to raw CSV results file")
    parser.add_argument("--out", type=str, default="experiments/results", help="Output directory")
    args = parser.parse_args()

    analyze_and_plot_results(args.csv, args.out)
