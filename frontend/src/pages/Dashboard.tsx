import { useEffect, useState } from 'react';
import { getCohort } from '../services/api';
import type { CohortSummary } from '../types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import StatCard from '../components/StatCard';

export default function Dashboard() {
  const [cohort, setCohort] = useState<CohortSummary[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCohort()
      .then(d => { setCohort(d); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <LoadingSpinner message="Loading cohort data…" />;
  if (error)   return <ErrorAlert message={error} />;

  const totalSubjects = cohort!.reduce((s, d) => s + d.n_human_subjects, 0);
  const totalObs      = cohort!.reduce((s, d) => s + d.n_valid_pk_observations, 0);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Research Dashboard</h1>
      <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: 24 }}>
        Validated Phase 5D frozen dataset summary.
      </p>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 32 }}>
        <StatCard label="Drugs"             value={cohort!.length} sub="7 validated" />
        <StatCard label="Human Subjects"    value={totalSubjects.toLocaleString()} colorClass="text-emerald-600" />
        <StatCard label="PK Observations"   value={totalObs.toLocaleString()} colorClass="text-violet-600" />
        <StatCard label="Target Proteins"   value="196" sub="ChEMBL unique" colorClass="text-orange-500" />
        <StatCard label="Network Edges"     value="222" sub="Validated interactions" colorClass="text-rose-500" />
      </div>

      {/* Cohort table */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)', marginBottom: 24 }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #f1f5f9' }}>
          <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>Validated Cohort — 7 Drugs</h3>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Drug Name', 'Human Subjects', 'PK Observations'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0.65rem 1.5rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cohort!.map((d, i) => (
              <tr key={d.drug_name} style={{ borderTop: '1px solid #f1f5f9', background: i % 2 === 0 ? '#fff' : '#fafbfc' }}>
                <td style={{ padding: '0.75rem 1.5rem', fontWeight: 600, color: '#1e293b' }}>{d.drug_name}</td>
                <td style={{ padding: '0.75rem 1.5rem', color: '#475569' }}>{d.n_human_subjects}</td>
                <td style={{ padding: '0.75rem 1.5rem', color: '#475569' }}>{d.n_valid_pk_observations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Key findings */}
      <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: '1.25rem 1.5rem' }}>
        <p style={{ fontWeight: 700, color: '#166534', fontSize: '0.9rem', marginBottom: 8 }}>✓ Key Validated Findings</p>
        <ul style={{ fontSize: '0.84rem', color: '#166534', lineHeight: 2, paddingLeft: 16 }}>
          <li>SVD r=2 captures ≥93.8% of peak-normalized trajectory variance.</li>
          <li>Ward linkage cophenetic correlation = 0.944 — stable 2-cluster partition.</li>
          <li>Cluster 1 (rapid IV clearance): cefamandole, indomethacin, remifentanil, xanomeline.</li>
          <li>Cluster 2 (extended oral elimination): phenobarbital, quinidine, theophylline.</li>
          <li>Mantel p-values range 0.305–0.768 — <strong>no significant PK–target coupling detected</strong> (exploratory).</li>
        </ul>
      </div>
    </div>
  );
}
