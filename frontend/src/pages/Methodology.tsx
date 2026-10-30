const S = {
  wrap: { maxWidth: 760, margin: '0 auto' } as React.CSSProperties,
  h1: { fontSize: '1.6rem', fontWeight: 800, color: '#1e293b', marginBottom: '0.5rem' } as React.CSSProperties,
  sub: { color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' } as React.CSSProperties,
  card: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.5rem', marginBottom: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.04)' } as React.CSSProperties,
  h3: { fontSize: '1rem', fontWeight: 700, color: '#1e40af', marginBottom: 8 } as React.CSSProperties,
  p: { fontSize: '0.87rem', color: '#475569', lineHeight: 1.7 } as React.CSSProperties,
  tag: { display: 'inline-block', background: '#eff6ff', color: '#2563eb', borderRadius: 6, padding: '0.15rem 0.55rem', fontSize: '0.75rem', fontWeight: 600, marginRight: 6, marginTop: 6 } as React.CSSProperties,
  badge: { display: 'inline-block', background: '#fef3c7', color: '#92400e', borderRadius: 6, padding: '0.15rem 0.55rem', fontSize: '0.75rem', fontWeight: 600 } as React.CSSProperties,
};

export default function Methodology() {
  return (
    <div style={S.wrap}>
      <h1 style={S.h1}>Research Methodology</h1>
      <p style={S.sub}>End-to-end analytical pipeline — Phase 1 through Phase 5D</p>

      {[
        {
          step: '1 — Dataset',
          title: 'Open PK Data Acquisition & Validation',
          body: 'Plasma/serum concentration–time series were sourced from PK-DB for 7 drugs with continuous C(t) measurements. All 452 subjects were aggregated to drug-level mean trajectories on a 15-timepoint standard grid (0–24 h). Dose and peak normalizations were applied independently.',
          tags: ['7 drugs', '452 subjects', '5,174 observations', 'Phase 4D PASS'],
        },
        {
          step: '2 — SVD / DMD',
          title: 'Matrix Decomposition — SVD and DMD',
          body: 'A 7×15 drug-by-time concentration matrix was subjected to truncated Singular Value Decomposition (rank r=2, capturing ≥93.8% variance). Discrete Dynamic Mode Decomposition extracted temporal state transition modes. Low-rank SVD scores serve as compact pharmacokinetic fingerprints for each drug.',
          tags: ['SVD r=2', '93.8% variance', 'Discrete DMD', 'Dose & Peak norms'],
        },
        {
          step: '3 — PK Similarity',
          title: 'Pairwise PK Distance Matrices',
          body: 'Three pairwise distance representations were computed: SVD Peak Distance (Euclidean on peak-normalized SVD scores), SVD Dose Distance (Euclidean on dose-normalized SVD scores), and DTW Peak Distance (Dynamic Time Warping on peak-normalized trajectories). These yield 7×7 symmetric distance matrices.',
          tags: ['SVD Peak Dist', 'SVD Dose Dist', 'DTW Peak Dist', '21 unique pairs'],
        },
        {
          step: '4 — ChEMBL Network',
          title: 'Drug–Target Bipartite Network',
          body: 'ChEMBL identifiers were mapped for all 7 drugs. Curated Mechanisms of Action and high-confidence bioassay activities (pChEMBL ≥5.0, IC₅₀/Kᵢ ≤10 μM) were harvested. A 7×196 binary interaction matrix was constructed. Pairwise Jaccard and Cosine target profile similarities were computed.',
          tags: ['196 targets', '222 edges', 'Jaccard sim', 'Cosine sim', '100% mapped'],
        },
        {
          step: '5 — Clustering',
          title: 'PK Trajectory Clustering',
          body: 'Agglomerative hierarchical clustering (Ward and Average linkage) and k-Means (k=2,3) were applied to SVD scores and DTW distance matrices. Cophenetic correlation (Ward: 0.944, Average: 0.951) and silhouette scores (best: 0.630) confirm clean mathematical partitioning. Clusters reflect kinetic morphology only — not biological interaction.',
          tags: ['Ward linkage', 'Avg linkage', 'k-Means k=2,3', 'Silhouette 0.630'],
        },
        {
          step: '6 — Coupling',
          title: 'PK–Target Analytical Coupling (Mantel Test)',
          body: 'Non-parametric Mantel matrix permutation tests (10,000 permutations, seed=42) quantified correlation between PK distance matrices and target distance matrices. Spearman ρ and Pearson r were also computed. All findings are classified EXPLORATORY — no statistically significant coupling was detected (Mantel p > 0.30 for all representations).',
          tags: ['10,000 permutations', 'Mantel test', 'Spearman ρ', 'Pearson r'],
          badge: 'Non-significant (p > 0.30)',
        },
      ].map(({ step, title, body, tags, badge }) => (
        <div key={step} style={S.card}>
          <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{step}</p>
          <h3 style={S.h3}>{title}</h3>
          <p style={S.p}>{body}</p>
          <div style={{ marginTop: 10 }}>
            {tags.map(t => <span key={t} style={S.tag}>{t}</span>)}
            {badge && <span style={{ ...S.badge, marginLeft: 6 }}>{badge}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
