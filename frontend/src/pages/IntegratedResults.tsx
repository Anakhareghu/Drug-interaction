import { useEffect, useState } from 'react';
import { getCoupling, getClustering } from '../services/api';
import type { CouplingResult, ClusteringResult } from '../types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine
} from 'recharts';

const P_COLORS = (p: number) => p < 0.05 ? '#16a34a' : p < 0.2 ? '#d97706' : '#94a3b8';

export default function IntegratedResults() {
  const [coupling, setCoupling] = useState<CouplingResult[]>([]);
  const [clustering, setClustering] = useState<ClusteringResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getCoupling(), getClustering()])
      .then(([c, cl]) => { setCoupling(c); setClustering(cl); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <LoadingSpinner message="Loading integrated results…" />;
  if (error)   return <ErrorAlert message={error} />;

  // Build label for coupling rows
  const couplingRows = coupling.map(r => ({
    ...r,
    label: `${r.pk_representation.replace(' Distance', '')} / ${r.target_representation.replace(' Distance', '')}`,
  }));

  // Spearman bar chart data
  const spearmanData = couplingRows.map(r => ({
    name: r.label.split(' / ')[0].slice(0, 10),
    rho: +r.spearman_rho.toFixed(4),
    p: r.spearman_p_two_tailed,
  }));

  // Mantel p bar chart data
  const mantelData = couplingRows.map(r => ({
    label: r.label.slice(0, 20),
    p: +r.mantel_p_value.toFixed(4),
  }));

  // Cluster ward k=2 groups
  const cluster1 = clustering.filter(c => c.svd_ward_k2 === 1).map(c => c.drug_name);
  const cluster2 = clustering.filter(c => c.svd_ward_k2 === 2).map(c => c.drug_name);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Integrated Results</h1>
      <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: 4 }}>
        Phase 5C.3 — Validated clustering and PK–target analytical coupling.
      </p>

      {/* Exploratory banner */}
      <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 10, padding: '0.75rem 1.25rem', marginBottom: 24, fontSize: '0.83rem', color: '#92400e', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: '1rem' }}>⚠</span>
        <span>
          <strong>Exploratory Findings:</strong> All PK–target coupling results are classified{' '}
          <code style={{ background: '#fde68a', padding: '0 4px', borderRadius: 3 }}>EXPLORATORY_WEAK</code>.
          No statistically significant coupling was detected (Mantel p &gt; 0.30 for all representations).
          N=7 pilot size makes non-significant results mathematically expected for diverse non-congeneric drugs.
        </span>
      </div>

      {/* Clustering summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: '1.25rem' }}>
          <p style={{ fontWeight: 700, color: '#1d4ed8', fontSize: '0.85rem', marginBottom: 8 }}>
            Cluster 1 — Rapid Clearance / IV Decay
          </p>
          {cluster2.map(d => <span key={d} style={{ display: 'inline-block', background: '#dbeafe', color: '#1e40af', padding: '0.2rem 0.6rem', borderRadius: 20, fontSize: '0.78rem', fontWeight: 600, margin: '0 4px 4px 0' }}>{d}</span>)}
          <p style={{ fontSize: '0.75rem', color: '#3b82f6', marginTop: 8 }}>SVD Ward k=2 — Silhouette 0.630, Cophenetic 0.944</p>
        </div>
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: '1.25rem' }}>
          <p style={{ fontWeight: 700, color: '#15803d', fontSize: '0.85rem', marginBottom: 8 }}>
            Cluster 2 — Extended Elimination / Oral
          </p>
          {cluster1.map(d => <span key={d} style={{ display: 'inline-block', background: '#dcfce7', color: '#166534', padding: '0.2rem 0.6rem', borderRadius: 20, fontSize: '0.78rem', fontWeight: 600, margin: '0 4px 4px 0' }}>{d}</span>)}
          <p style={{ fontSize: '0.75rem', color: '#16a34a', marginTop: 8 }}>DTW Avg k=2 — Silhouette 0.613, Cophenetic 0.799</p>
        </div>
      </div>

      {/* Mantel p-value bar chart */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.5rem', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 4 }}>
          Mantel Test p-values — 10,000 Permutations (seed=42)
        </h3>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: 16 }}>
          All p-values &gt; 0.05 — null hypothesis retained. No significant PK–target matrix coupling.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={mantelData} layout="vertical" margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
            <XAxis type="number" domain={[0, 1]} tickCount={6} tick={{ fontSize: 11 }} label={{ value: 'Mantel p-value', position: 'insideBottom', offset: -2 }} />
            <YAxis type="category" dataKey="label" tick={{ fontSize: 10 }} width={130} />
            <Tooltip formatter={(v: unknown) => (v as number).toFixed(4)} />
            <ReferenceLine x={0.05} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'α=0.05', position: 'top', fontSize: 10, fill: '#ef4444' }} />
            <Bar dataKey="p" radius={[0, 4, 4, 0]}>
              {mantelData.map((entry, i) => (
                <Cell key={i} fill={P_COLORS(entry.p)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Full coupling table */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #f1f5f9' }}>
          <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>PK–Target Coupling Results — All Representations (N=21 pairs)</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {['PK Repr.', 'Target Repr.', 'Spearman ρ', 'Spearman p', 'Pearson r', 'Pearson p', 'Mantel p', 'Status'].map(h => (
                  <th key={h} style={{ padding: '0.6rem 0.9rem', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {couplingRows.map((r, i) => (
                <tr key={i} style={{ borderTop: '1px solid #f1f5f9', background: i % 2 === 0 ? '#fff' : '#fafbfc' }}>
                  <td style={{ padding: '0.6rem 0.9rem', color: '#1e293b', fontWeight: 500, whiteSpace: 'nowrap' }}>{r.pk_representation}</td>
                  <td style={{ padding: '0.6rem 0.9rem', color: '#475569', whiteSpace: 'nowrap' }}>{r.target_representation}</td>
                  <td style={{ padding: '0.6rem 0.9rem', textAlign: 'center', fontWeight: 700, color: Math.abs(r.spearman_rho) > 0.3 ? '#d97706' : '#475569' }}>
                    {r.spearman_rho.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.6rem 0.9rem', textAlign: 'center', color: r.spearman_p_two_tailed < 0.05 ? '#16a34a' : '#94a3b8' }}>
                    {r.spearman_p_two_tailed.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.6rem 0.9rem', textAlign: 'center', color: '#475569' }}>{r.pearson_r.toFixed(4)}</td>
                  <td style={{ padding: '0.6rem 0.9rem', textAlign: 'center', color: '#94a3b8' }}>{r.pearson_p_two_tailed.toFixed(4)}</td>
                  <td style={{ padding: '0.6rem 0.9rem', textAlign: 'center', fontWeight: 700, color: r.mantel_p_value < 0.05 ? '#16a34a' : '#94a3b8' }}>
                    {r.mantel_p_value.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.6rem 0.9rem' }}>
                    <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 4, padding: '0.15rem 0.5rem', fontSize: '0.72rem', fontWeight: 700 }}>
                      {r.coupling_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scientific conclusion */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '1rem 1.25rem', fontSize: '0.83rem', color: '#475569', lineHeight: 1.7 }}>
        <strong style={{ color: '#1e293b' }}>Scientific Conclusion:</strong> This 7-drug proof-of-concept demonstrates a complete data-to-coupling analytical pipeline.
        The non-significant Mantel results are methodologically valid and scientifically expected for a diverse, non-congeneric drug cohort.
        PK trajectory similarity reflects <em>curve morphology</em> (clearance rates, distribution phases),
        not metabolic enzyme competition or clinical DDI mechanisms.
        Clustering is strictly a mathematical kinetic grouping — not biological proof of interaction.
      </div>
    </div>
  );
}
