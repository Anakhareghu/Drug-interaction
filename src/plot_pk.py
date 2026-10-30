"""
plot_pk.py
==========
Phase 2 — Concentration-vs-Time Trajectory Visualization

Generates concentration-vs-time plots for representative usable drugs
from the cleaned Phase 2 dataset (data/processed/pk_timecourses_clean.csv).

Saves figure outputs to outputs/figures/.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

WORKSPACE_DIR = Path(__file__).parent.parent
CLEAN_DATA = WORKSPACE_DIR / "data" / "processed" / "pk_timecourses_clean.csv"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set matplotlib style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

def plot_single_drug(df_drug, drug_name, filename):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    
    # Group by study or source_table
    studies = df_drug["study_sid"].unique()
    colors = plt.cm.Set2(np.linspace(0, 1, max(len(studies), 1)))
    
    for idx, study in enumerate(studies):
        sub_df = df_drug[df_drug["study_sid"] == study].sort_values(by="time_hr")
        ax.plot(
            sub_df["time_hr"],
            sub_df["value_std"],
            marker="o",
            linestyle="-",
            linewidth=1.8,
            markersize=5,
            color=colors[idx],
            label=f"Study: {study} ({len(sub_df)} pts)",
            alpha=0.85,
        )
        
    unit_str = df_drug["unit_std"].iloc[0] if len(df_drug) > 0 else "standardized"
    ax.set_title(f"Pharmacokinetic Concentration-Time Profile: {drug_name.capitalize()}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Time (hours)", fontsize=11, labelpad=8)
    ax.set_ylabel(f"Concentration ({unit_str})", fontsize=11, labelpad=8)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=9)
    plt.tight_layout()
    
    out_path = FIGURES_DIR / filename
    plt.savefig(out_path)
    plt.close()
    print(f"Saved figure: {out_path}")


def plot_combined_grid(df_clean, top_drugs, filename="multi_drug_pk_profiles.png"):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), dpi=300)
    axes = axes.flatten()
    
    for idx, d_name in enumerate(top_drugs[:6]):
        ax = axes[idx]
        sub_df = df_clean[df_clean["pkdb_id"] == d_name].sort_values(by="time_hr")
        if len(sub_df) == 0:
            continue
            
        unit_str = sub_df["unit_std"].iloc[0]
        studies = sub_df["study_sid"].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, max(len(studies), 1)))
        
        for s_idx, study in enumerate(studies):
            st_df = sub_df[sub_df["study_sid"] == study].sort_values(by="time_hr")
            ax.plot(st_df["time_hr"], st_df["value_std"], marker="o", markersize=4, linestyle="-", linewidth=1.5, color=colors[s_idx], alpha=0.8)
            
        ax.set_title(f"{d_name.capitalize()} (n={len(sub_df)})", fontsize=11, fontweight="bold")
        ax.set_xlabel("Time (hr)", fontsize=9)
        ax.set_ylabel(f"Conc ({unit_str})", fontsize=9)
        ax.tick_params(labelsize=8)
        
    plt.suptitle("Representative Pharmacokinetic Trajectories across Candidate Drugs", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    
    out_path = FIGURES_DIR / filename
    plt.savefig(out_path)
    plt.close()
    print(f"Saved combined summary plot: {out_path}")


def main():
    if not CLEAN_DATA.exists():
        print(f"Cleaned dataset not found: {CLEAN_DATA}")
        return
        
    df_clean = pd.read_csv(CLEAN_DATA)
    print(f"Loaded {len(df_clean)} cleaned PK observations across {df_clean['drug_name'].nunique()} drugs.")
    
    # Generate individual plots for top usable drugs
    target_drugs = ["midazolam", "omeprazole", "losartan", "dapagliflozin", "canagliflozin", "metoprolol"]
    
    for d_sid in target_drugs:
        sub_df = df_clean[df_clean["pkdb_id"] == d_sid]
        if len(sub_df) > 0:
            plot_single_drug(sub_df, d_sid, f"pk_profile_{d_sid}.png")
            
    plot_combined_grid(df_clean, target_drugs, "summary_pk_trajectories.png")
    print("Completed all figure generation.")

if __name__ == "__main__":
    main()
