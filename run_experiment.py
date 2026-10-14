#!/usr/bin/env python3
"""
Master Execution Script for the Risk-Aware ZTNA Experimental Testbed.

Runs the full end-to-end experiment:
  1. Traffic generation (legitimate vs. attack scenarios)
  2. 30x repetitions of evaluation across 3 configurations
  3. Raw measurements export to CSV
  4. Statistical analysis & plot generation
"""

from __future__ import annotations

import os
from pathlib import Path

from experiments.analysis import analyze_and_plot_results
from experiments.benchmark_runner import ExperimentRunner

def main() -> None:
    print("================================================================")
    print(" Risk-Aware ZTNA with Adaptive MFA - Master Experiment Harness")
    print("================================================================\n")

    output_dir = Path("experiments/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1/3: Initializing testbed subsystems in memory...")
    runner = ExperimentRunner(
        output_dir=str(output_dir),
        num_repetitions=30,      # Strict minimum for valid statistical CI
        requests_per_rep=100     # 3000 total evaluations per config
    )

    print("Step 2/3: Executing 30 repetitive benchmark rounds across 3 configurations...")
    print("  - Generating reproducible synthetic traffic (seed fixed per repetition).")
    print("  - Evaluating A: Baseline VPN")
    print("  - Evaluating B: Static MFA")
    print("  - Evaluating C: Proposed Risk-Aware ZTNA\n")

    csv_file = runner.execute_all_repetitions()

    print("\nStep 3/3: Running statistical analysis and rendering charts...")
    analyze_and_plot_results(csv_path=csv_file, output_dir=str(output_dir))

    print("\nExperiment Harness Completed Successfully!")
    print(f"Check the '{output_dir}' directory for CSVs, Markdown summaries, and PNG plots.")

if __name__ == "__main__":
    main()
