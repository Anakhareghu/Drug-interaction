"""
perform_phase5b_decomposition.py
=================================
Phase 5B — Singular Value Decomposition (SVD) & Dynamic Mode Decomposition (DMD) Engine

Executes SVD and discrete-snapshot DMD on both candidate 7x15 modeling matrices:
  1. Dose-Normalized Matrix (C / Dose_mg)
  2. Peak-Normalized Matrix (C / Cmax)

Outputs:
  - Processed CSV files in data/processed/phase5b/
  - Publication-quality figures in outputs/figures/phase5b/
  - Report in PHASE_5B_STATUS.md

Usage:
    python src/perform_phase5b_decomposition.py
"""

import os
import numpy as np
import pandas as pd
import scipy.linalg as la
import matplotlib.pyplot as plt
from pathlib import Path

# Setup directories
WORKSPACE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
PHASE5B_DATA_DIR = PROCESSED_DIR / "phase5b"
FIGURES_DIR = WORKSPACE_DIR / "outputs" / "figures" / "phase5b"

PHASE5B_DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DOSE_MAT_PATH = PROCESSED_DIR / "pk_phase5_dose_normalized_matrix.csv"
PEAK_MAT_PATH = PROCESSED_DIR / "pk_phase5_peak_normalized_matrix.csv"

VALIDATED_DRUGS = ["cefamandole", "indomethacin", "phenobarbital", "quinidine", "remifentanil", "theophylline", "xanomeline"]
T_GRID = np.array([0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0])

def run_phase5b_decomposition():
    print("=== PHASE 5B: SVD & DYNAMIC MODE DECOMPOSITION ===")
    
    # ----------------------------------------------------
    # STAGE A: INPUT VALIDATION
    # ----------------------------------------------------
    print("\n[STAGE A] Loading and Validating Input Candidate Matrices...")
    if not DOSE_MAT_PATH.exists() or not PEAK_MAT_PATH.exists():
        raise FileNotFoundError("Candidate matrix files missing! Ensure Phase 5A has completed.")
        
    df_dose = pd.read_csv(DOSE_MAT_PATH, index_col="drug_name")
    df_peak = pd.read_csv(PEAK_MAT_PATH, index_col="drug_name")
    
    # Assert integrity
    for name, df in [("Dose-Normalized", df_dose), ("Peak-Normalized", df_peak)]:
        assert df.shape == (7, 15), f"{name} matrix shape mismatch! Expected (7, 15), got {df.shape}"
        assert list(df.index) == VALIDATED_DRUGS, f"{name} matrix drug index mismatch!"
        assert df.isna().sum().sum() == 0, f"{name} matrix contains NaNs!"
        assert not np.isinf(df.values).any(), f"{name} matrix contains Infs!"
        print(f"  Verified {name} Matrix: Shape (7, 15), 0 NaNs, 0 Infs.")

    # ----------------------------------------------------
    # STAGE B: SVD DECOMPOSITION
    # ----------------------------------------------------
    print("\n[STAGE B] Computing Singular Value Decomposition (SVD)...")
    
    svd_results = {}
    
    for norm_type, df_mat in [("dose", df_dose), ("peak", df_peak)]:
        X = df_mat.values
        U, s, Vt = la.svd(X, full_matrices=False)
        var = s**2
        exp_var = var / np.sum(var)
        cum_var = np.cumsum(exp_var)
        cond = s[0] / s[-1] if s[-1] > 0 else np.nan
        rank = np.linalg.matrix_rank(X)
        
        # Calculate low-rank reconstruction errors
        f_norm = la.norm(X, "fro")
        recon_errors = []
        for r in range(1, len(s) + 1):
            Xr = U[:, :r] @ np.diag(s[:r]) @ Vt[:r, :]
            err_f = la.norm(X - Xr, "fro")
            rel_err = err_f / f_norm
            recon_errors.append({
                "norm_type": norm_type,
                "rank": r,
                "frob_error": round(err_f, 6),
                "rel_frob_error": round(rel_err, 6),
                "cum_explained_var": round(cum_var[r-1], 6)
            })
            
        svd_results[norm_type] = {
            "X": X, "U": U, "s": s, "Vt": Vt,
            "exp_var": exp_var, "cum_var": cum_var,
            "cond": cond, "rank": rank,
            "recon_errors": pd.DataFrame(recon_errors)
        }
        
        print(f"  {norm_type.upper()} SVD: s1={s[0]:.4f}, s2={s[1]:.4f}, s3={s[2]:.4f}")
        print(f"    Explained Var: PC1={exp_var[0]*100:.2f}%, PC2={exp_var[1]*100:.2f}%, PC3={exp_var[2]*100:.2f}%")
        print(f"    Cum Var: PC1-2={cum_var[1]*100:.2f}%, PC1-3={cum_var[2]*100:.2f}%")

    # Export SVD CSV Files
    df_s_vals = pd.DataFrame({
        "component": np.arange(1, 8),
        "dose_singular_value": svd_results["dose"]["s"],
        "peak_singular_value": svd_results["peak"]["s"]
    })
    df_s_vals.to_csv(PHASE5B_DATA_DIR / "svd_singular_values.csv", index=False)
    
    df_exp_var = pd.DataFrame({
        "component": np.arange(1, 8),
        "dose_exp_var_ratio": svd_results["dose"]["exp_var"],
        "dose_cum_var_ratio": svd_results["dose"]["cum_var"],
        "peak_exp_var_ratio": svd_results["peak"]["exp_var"],
        "peak_cum_var_ratio": svd_results["peak"]["cum_var"]
    })
    df_exp_var.to_csv(PHASE5B_DATA_DIR / "svd_explained_variance.csv", index=False)
    
    # Export U matrices (Drug Loadings)
    df_u_dose = pd.DataFrame(svd_results["dose"]["U"], index=VALIDATED_DRUGS, columns=[f"U{i+1}" for i in range(7)])
    df_u_peak = pd.DataFrame(svd_results["peak"]["U"], index=VALIDATED_DRUGS, columns=[f"U{i+1}" for i in range(7)])
    df_u_dose.to_csv(PHASE5B_DATA_DIR / "svd_u_matrix_dose.csv")
    df_u_peak.to_csv(PHASE5B_DATA_DIR / "svd_u_matrix_peak.csv")
    
    # Export Vt matrices (Temporal Modes)
    df_vt_dose = pd.DataFrame(svd_results["dose"]["Vt"], index=[f"Mode{i+1}" for i in range(7)], columns=[f"{t}h" for t in T_GRID])
    df_vt_peak = pd.DataFrame(svd_results["peak"]["Vt"], index=[f"Mode{i+1}" for i in range(7)], columns=[f"{t}h" for t in T_GRID])
    df_vt_dose.to_csv(PHASE5B_DATA_DIR / "svd_vt_matrix_dose.csv")
    df_vt_peak.to_csv(PHASE5B_DATA_DIR / "svd_vt_matrix_peak.csv")
    
    # Export SVD Scores (U * S)
    scores_dose = svd_results["dose"]["U"] @ np.diag(svd_results["dose"]["s"])
    scores_peak = svd_results["peak"]["U"] @ np.diag(svd_results["peak"]["s"])
    pd.DataFrame(scores_dose, index=VALIDATED_DRUGS, columns=[f"Score{i+1}" for i in range(7)]).to_csv(PHASE5B_DATA_DIR / "svd_scores_dose.csv")
    pd.DataFrame(scores_peak, index=VALIDATED_DRUGS, columns=[f"Score{i+1}" for i in range(7)]).to_csv(PHASE5B_DATA_DIR / "svd_scores_peak.csv")
    
    # Export Reconstruction Errors
    df_recon_all = pd.concat([svd_results["dose"]["recon_errors"], svd_results["peak"]["recon_errors"]], ignore_index=True)
    df_recon_all.to_csv(PHASE5B_DATA_DIR / "svd_reconstruction_errors.csv", index=False)
    
    print(f"  Saved SVD CSV datasets to {PHASE5B_DATA_DIR}")

    # ----------------------------------------------------
    # STAGE C: DYNAMIC MODE DECOMPOSITION (DMD)
    # ----------------------------------------------------
    print("\n[STAGE C] Computing Discrete-Snapshot Dynamic Mode Decomposition (DMD)...")
    
    dmd_results = {}
    dmd_evals_list = []
    
    for norm_type, df_mat in [("dose", df_dose), ("peak", df_peak)]:
        X = df_mat.values
        X1 = X[:, :-1]
        X2 = X[:, 1:]
        
        # Rank r=3 truncated DMD
        rank = 3
        U, s, Vt = la.svd(X1, full_matrices=False)
        r = min(rank, len(s))
        Ur = U[:, :r]
        Sr = np.diag(s[:r])
        Vtr = Vt[:r, :]
        
        A_tilde = Ur.T @ X2 @ Vtr.T @ np.linalg.inv(Sr)
        evals, evecs = la.eig(A_tilde)
        
        # Sort eigenvalues by magnitude
        idx_sort = np.argsort(np.abs(evals))[::-1]
        evals = evals[idx_sort]
        evecs = evecs[:, idx_sort]
        
        Phi = X2 @ Vtr.T @ np.linalg.inv(Sr) @ evecs
        
        x1 = X1[:, 0]
        b, _, _, _ = la.lstsq(Phi, x1)
        
        K = X.shape[1]
        X_dmd = np.zeros((X.shape[0], K), dtype=complex)
        for k in range(K):
            X_dmd[:, k] = Phi @ np.diag(evals**k) @ b
            
        X_dmd_real = np.real(X_dmd)
        rel_err = la.norm(X - X_dmd_real, "fro") / la.norm(X, "fro")
        
        dmd_results[norm_type] = {
            "evals": evals, "evecs": evecs, "Phi": Phi, "b": b,
            "X_dmd": X_dmd_real, "rel_err": rel_err
        }
        
        for i, ev in enumerate(evals):
            dmd_evals_list.append({
                "norm_type": norm_type,
                "mode_index": i + 1,
                "real_part": round(float(np.real(ev)), 6),
                "imag_part": round(float(np.imag(ev)), 6),
                "magnitude": round(float(np.abs(ev)), 6),
                "phase_rad": round(float(np.angle(ev)), 6)
            })
            
        print(f"  {norm_type.upper()} DMD (r={r}): Eigenvalue magnitudes = {np.round(np.abs(evals), 4)}")
        print(f"    Relative DMD Reconstruction Error = {rel_err*100:.2f}%")

    df_dmd_evals = pd.DataFrame(dmd_evals_list)
    df_dmd_evals.to_csv(PHASE5B_DATA_DIR / "dmd_eigenvalues.csv", index=False)
    
    # Save DMD reconstructions
    pd.DataFrame(dmd_results["dose"]["X_dmd"], index=VALIDATED_DRUGS, columns=[f"{t}h" for t in T_GRID]).to_csv(PHASE5B_DATA_DIR / "dmd_reconstructions_dose.csv")
    pd.DataFrame(dmd_results["peak"]["X_dmd"], index=VALIDATED_DRUGS, columns=[f"{t}h" for t in T_GRID]).to_csv(PHASE5B_DATA_DIR / "dmd_reconstructions_peak.csv")

    # ----------------------------------------------------
    # STAGE D: PUBLICATION-QUALITY FIGURES GENERATION
    # ----------------------------------------------------
    print("\n[STAGE D] Generating Publication-Quality Decomposition Figures...")
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    # 1. Singular Value Spectrum
    plt.figure(figsize=(8, 5))
    comps = np.arange(1, 8)
    plt.plot(comps, svd_results["dose"]["s"], "o-", color="#1f77b4", linewidth=2, markersize=8, label="Dose-Normalized")
    plt.plot(comps, svd_results["peak"]["s"], "s--", color="#ff7f0e", linewidth=2, markersize=8, label="Peak-Normalized")
    plt.title("SVD Singular Value Spectrum", fontsize=14, fontweight="bold")
    plt.xlabel("Component Index", fontsize=12)
    plt.ylabel("Singular Value (σ)", fontsize=12)
    plt.xticks(comps)
    plt.yscale("log")
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_singular_values.png", dpi=300)
    plt.close()
    
    # 2. Cumulative Explained Variance
    plt.figure(figsize=(8, 5))
    plt.plot(comps, svd_results["dose"]["cum_var"]*100, "o-", color="#1f77b4", linewidth=2, markersize=8, label="Dose-Normalized")
    plt.plot(comps, svd_results["peak"]["cum_var"]*100, "s--", color="#ff7f0e", linewidth=2, markersize=8, label="Peak-Normalized")
    plt.axhline(90, color="gray", linestyle=":", label="90% Variance Threshold")
    plt.axhline(95, color="red", linestyle="--", label="95% Variance Threshold")
    plt.title("SVD Cumulative Explained Variance", fontsize=14, fontweight="bold")
    plt.xlabel("Number of Singular Components", fontsize=12)
    plt.ylabel("Cumulative Variance (%)", fontsize=12)
    plt.xticks(comps)
    plt.ylim(75, 102)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_explained_variance.png", dpi=300)
    plt.close()

    # 3. Temporal SVD Modes (First 3 Right Singular Vectors V^T)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for idx, (norm_type, label, color_style) in enumerate([("dose", "Dose-Normalized", "blue"), ("peak", "Peak-Normalized", "orange")]):
        Vt = svd_results[norm_type]["Vt"]
        ax = axes[idx]
        ax.plot(T_GRID, Vt[0, :], "o-", label="Mode 1 (PC1)")
        ax.plot(T_GRID, Vt[1, :], "s--", label="Mode 2 (PC2)")
        ax.plot(T_GRID, Vt[2, :], "^-.", label="Mode 3 (PC3)")
        ax.set_title(f"{label} Temporal SVD Modes", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time (hours)", fontsize=11)
        if idx == 0:
            ax.set_ylabel("Mode Value (V^T)", fontsize=11)
        ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_temporal_modes.png", dpi=300)
    plt.close()

    # 4. Drug Scores / Loadings Scatter Plot (PC1 vs PC2)
    plt.figure(figsize=(9, 6))
    scores_p = scores_peak[:, :2]
    plt.scatter(scores_p[:, 0], scores_p[:, 1], color="#2ca02c", s=120, zorder=3)
    for i, drug in enumerate(VALIDATED_DRUGS):
        plt.annotate(drug, (scores_p[i, 0] + 0.05, scores_p[i, 1] + 0.03), fontsize=11, fontweight="bold")
    plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
    plt.axvline(0, color="black", linewidth=0.8, linestyle="--")
    plt.title("Drug Scores Projection in Peak-Normalized SVD Space (PC1 vs PC2)", fontsize=13, fontweight="bold")
    plt.xlabel(f"PC1 ({svd_results['peak']['exp_var'][0]*100:.1f}% Variance)", fontsize=11)
    plt.ylabel(f"PC2 ({svd_results['peak']['exp_var'][1]*100:.1f}% Variance)", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_drug_loadings.png", dpi=300)
    plt.close()

    # 5. DMD Eigenvalues in Complex Unit Circle
    plt.figure(figsize=(7, 7))
    theta = np.linspace(0, 2*np.pi, 200)
    plt.plot(np.cos(theta), np.sin(theta), "k--", label="Unit Circle (|μ| = 1)")
    
    ev_d = dmd_results["dose"]["evals"]
    ev_p = dmd_results["peak"]["evals"]
    plt.scatter(np.real(ev_d), np.imag(ev_d), color="#1f77b4", s=100, marker="o", label="Dose-Norm DMD Eigenvalues")
    plt.scatter(np.real(ev_p), np.imag(ev_p), color="#ff7f0e", s=100, marker="s", label="Peak-Norm DMD Eigenvalues")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.axvline(0, color="black", linewidth=0.8)
    plt.title("Discrete-Snapshot DMD Eigenvalue Spectrum", fontsize=13, fontweight="bold")
    plt.xlabel("Real(μ)", fontsize=11)
    plt.ylabel("Imag(μ)", fontsize=11)
    plt.xlim(-1.2, 1.2)
    plt.ylim(-1.2, 1.2)
    plt.legend(fontsize=10)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "dmd_eigenvalues.png", dpi=300)
    plt.close()

    # 6. Observed vs Reconstructed Trajectories
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    for i, drug in enumerate(VALIDATED_DRUGS):
        ax = axes[i]
        obs_curve = df_peak.loc[drug].values
        
        # Rank 2 SVD recon
        U_p = svd_results["peak"]["U"]
        s_p = svd_results["peak"]["s"]
        Vt_p = svd_results["peak"]["Vt"]
        svd_r2 = (U_p[i, :2] @ np.diag(s_p[:2]) @ Vt_p[:2, :])
        
        dmd_curve = dmd_results["peak"]["X_dmd"][i, :]
        
        ax.plot(T_GRID, obs_curve, "k-o", label="Observed", linewidth=2, markersize=5)
        ax.plot(T_GRID, svd_r2, "r--", label="SVD Rank 2", linewidth=1.8)
        ax.plot(T_GRID, dmd_curve, "b-.", label="DMD Rank 3", linewidth=1.8)
        ax.set_title(drug, fontsize=12, fontweight="bold")
        ax.set_xlabel("Time (h)", fontsize=10)
        ax.set_ylabel("C / Cmax", fontsize=10)
        if i == 0:
            ax.legend(fontsize=9)
    axes[7].axis("off")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_dmd_reconstructions.png", dpi=300)
    plt.close()

    # 7. Low-Rank Reconstruction Errors Curve
    plt.figure(figsize=(8, 5))
    ranks = svd_results["dose"]["recon_errors"]["rank"].values
    plt.plot(ranks, svd_results["dose"]["recon_errors"]["rel_frob_error"]*100, "o-", color="#1f77b4", linewidth=2, label="Dose-Normalized SVD Error")
    plt.plot(ranks, svd_results["peak"]["recon_errors"]["rel_frob_error"]*100, "s--", color="#ff7f0e", linewidth=2, label="Peak-Normalized SVD Error")
    plt.axhline(dmd_results["dose"]["rel_err"]*100, color="#1f77b4", linestyle=":", label="Dose DMD (r=3) Error")
    plt.axhline(dmd_results["peak"]["rel_err"]*100, color="#ff7f0e", linestyle=":", label="Peak DMD (r=3) Error")
    plt.title("Decomposition Reconstruction Error vs Rank", fontsize=14, fontweight="bold")
    plt.xlabel("Truncation Rank (r)", fontsize=12)
    plt.ylabel("Relative Frobenius Error (%)", fontsize=12)
    plt.xticks(ranks)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "svd_reconstruction_errors.png", dpi=300)
    plt.close()

    print(f"  Generated publication-quality figures in {FIGURES_DIR}")

    # Export Validation Summary CSV
    val_summary = []
    val_summary.append({"metric": "dose_svd_rank", "value": svd_results["dose"]["rank"]})
    val_summary.append({"metric": "dose_svd_pc1_var_pct", "value": round(svd_results["dose"]["exp_var"][0]*100, 4)})
    val_summary.append({"metric": "dose_svd_pc2_cum_var_pct", "value": round(svd_results["dose"]["cum_var"][1]*100, 4)})
    val_summary.append({"metric": "dose_svd_pc3_cum_var_pct", "value": round(svd_results["dose"]["cum_var"][2]*100, 4)})
    val_summary.append({"metric": "peak_svd_rank", "value": svd_results["peak"]["rank"]})
    val_summary.append({"metric": "peak_svd_pc1_var_pct", "value": round(svd_results["peak"]["exp_var"][0]*100, 4)})
    val_summary.append({"metric": "peak_svd_pc2_cum_var_pct", "value": round(svd_results["peak"]["cum_var"][1]*100, 4)})
    val_summary.append({"metric": "peak_svd_pc3_cum_var_pct", "value": round(svd_results["peak"]["cum_var"][2]*100, 4)})
    val_summary.append({"metric": "dose_dmd_r3_rel_err_pct", "value": round(dmd_results["dose"]["rel_err"]*100, 4)})
    val_summary.append({"metric": "peak_dmd_r3_rel_err_pct", "value": round(dmd_results["peak"]["rel_err"]*100, 4)})
    
    df_val_sum = pd.DataFrame(val_summary)
    df_val_sum.to_csv(PHASE5B_DATA_DIR / "phase5b_validation_summary.csv", index=False)

    print("\nPhase 5B SVD and DMD Decompositions completed successfully.")

if __name__ == "__main__":
    run_phase5b_decomposition()
