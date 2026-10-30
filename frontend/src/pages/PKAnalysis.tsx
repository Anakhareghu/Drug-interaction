import { useEffect, useState } from 'react';
import { getTrajectories, getSimilarity, getClustering } from '../services/api';
import type { PKTrajectory, PKSimilarity, ClusteringResult } from '../types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const PALETTE = ['#2563eb','#dc2626','#16a34a','#d97706','#7c3aed','#db2777','#0891b2'];

export default function PKAnalysis() {
  const [trajectories, setTrajectories] = useState<PKTrajectory[]>([]);
  const [similarity, setSimilarity] = useState<PKSimilarity[]>([]);
  const [clustering, setClustering] = useState<ClusteringResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getTrajectories(), getSimilarity(), getClustering()])
      .then(([t, s, c]) => {
        setTrajectories(t); setSimilarity(s); setClustering(c);
        setLoading(false);
      })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <LoadingSpinner message="Loading PK analysis data…" />;
  if (error)   return <ErrorAlert message={error} />;

  // Build multi-drug overlay chart data on peak-normalized trajectories
  const allTimes = Array.from(new Set(
    trajectories.flatMap(t => t.trajectory.map(p => p.time))
  )).sort((a, b) => a - b);

  const overlayData = allTimes.map(time => {
    const row: Record<string, number> = { time };
    trajectories.forEach(t => {
      const pt = t.trajectory.find(p => p.time === time);
      if (pt) row[t.drug_name] = +pt.peak_norm_mean.toFixed(4);
    });
    return row;
  });

  // Distance heatmap — unique SVD peak distances
  const drugs = clustering.map(c => c.drug_name);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>PK Analysis</h1>
      <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: 24 }}>
        Standardized concentration–time curves, SVD similarity distances, and clustering assignments.
      </p>

      {/* Multi-drug trajectory overlay */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.5rem', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 4 }}>
          Peak-Normalized PK Trajectories — All 7 Drugs
        </h3>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 16 }}>
          Each drug's mean concentration scaled to Cmax=1. Drug-level aggregates (no subject data shown).
        </p>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={overlayData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" label={{ value: 'Time (h)', position: 'insideBottom', offset: -3 }} tick={{ fontSize: 11 }} />
            <YAxis label={{ value: 'C(t) / Cmax', angle: -90, position: 'insideLeft', offset: 10 }} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: unknown) => (v as number).toFixed(4)} />
            <Legend />
            {trajectories.map((t, i) => (
              <Line key={t.drug_name} type="monotone" dataKey={t.drug_name}
                stroke={PALETTE[i % PALETTE.length]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Clustering table */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #f1f5f9' }}>
          <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>
            Cluster Assignments (SVD Ward linkage — k=2 canonical)
          </h3>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 2 }}>
            Mathematical kinetic partitioning only — not clinical drug-drug interaction.
          </p>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Drug','Ward k=2','Ward k=3','Avg k=2','Avg k=3','DTW k=2','k-Means k=2'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0.6rem 1rem', color: '#64748b', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clustering.map((c, i) => (
              <tr key={c.drug_name} style={{ borderTop: '1px solid #f1f5f9', background: i % 2 === 0 ? '#fff' : '#fafbfc' }}>
                <td style={{ padding: '0.65rem 1rem', fontWeight: 600, color: '#1e293b' }}>{c.drug_name}</td>
                {[c.svd_ward_k2, c.svd_ward_k3, c.svd_avg_k2, c.svd_avg_k3, c.dtw_avg_k2, c.kmeans_k2].map((v, j) => (
                  <td key={j} style={{ padding: '0.65rem 1rem', textAlign: 'center' }}>
                    <span style={{ background: v === 1 ? '#eff6ff' : '#fef3c7', color: v === 1 ? '#1d4ed8' : '#92400e', borderRadius: 4, padding: '0.15rem 0.5rem', fontWeight: 700, fontSize: '0.82rem' }}>
                      {v}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SVD distance matrix */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem 1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 12 }}>SVD Peak Distance — Pairwise</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ fontSize: '0.78rem', borderCollapse: 'collapse', minWidth: 500 }}>
            <thead>
              <tr>
                <th style={{ padding: '0.4rem 0.6rem', color: '#94a3b8' }}></th>
                {drugs.map(d => <th key={d} style={{ padding: '0.4rem 0.6rem', color: '#64748b', fontWeight: 600, textAlign: 'center', maxWidth: 70 }}>{d.slice(0, 6)}</th>)}
              </tr>
            </thead>
            <tbody>
              {drugs.map(drugA => (
                <tr key={drugA}>
                  <td style={{ padding: '0.4rem 0.6rem', fontWeight: 600, color: '#475569' }}>{drugA.slice(0, 8)}</td>
                  {drugs.map(drugB => {
                    const pair = similarity.find(s =>
                      (s.drug_name_1 === drugA && s.drug_name_2 === drugB) ||
                      (s.drug_name_1 === drugB && s.drug_name_2 === drugA)
                    );
                    const v = pair?.svd_distance_peak ?? (drugA === drugB ? 0 : null);
                    const intensity = v !== null ? Math.min(v / 5, 1) : 0;
                    return (
                      <td key={drugB} style={{
                        padding: '0.4rem 0.6rem', textAlign: 'center',
                        background: `rgba(37,99,235,${drugA === drugB ? 0 : intensity * 0.5})`,
                        color: intensity > 0.5 ? '#fff' : '#1e293b',
                        fontWeight: 500,
                      }}>
                        {v !== null ? v.toFixed(2) : '—'}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
