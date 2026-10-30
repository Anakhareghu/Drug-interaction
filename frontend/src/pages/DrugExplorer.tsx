import { useEffect, useState } from 'react';
import { getDrugs, getDrugInfo, getTrajectories } from '../services/api';
import type { DrugInfo, PKTrajectory } from '../types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#db2777', '#0891b2'];

export default function DrugExplorer() {
  const [drugs, setDrugs] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [info, setInfo] = useState<DrugInfo | null>(null);
  const [trajectories, setTrajectories] = useState<PKTrajectory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getDrugs(), getTrajectories()])
      .then(([d, t]) => {
        setDrugs(d);
        setSelected(d[0]);
        setTrajectories(t);
        setLoading(false);
      })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setInfoLoading(true);
    setInfoError(null);
    getDrugInfo(selected)
      .then(d => { setInfo(d); setInfoLoading(false); })
      .catch((e: Error) => { setInfoError(e.message); setInfoLoading(false); });
  }, [selected]);

  if (loading) return <LoadingSpinner message="Loading drug data…" />;
  if (error)   return <ErrorAlert message={error} />;

  const traj = trajectories.find(t => t.drug_name === selected);
  const chartData = traj?.trajectory.map(p => ({
    time: p.time,
    'Peak Norm': +p.peak_norm_mean.toFixed(4),
    'Dose Norm': +p.dose_norm_mean.toFixed(6),
  })) ?? [];

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Drug Explorer</h1>
      <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: 20 }}>
        Select a drug to view PK trajectory and ChEMBL information.
      </p>

      {/* Drug selector */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
        {drugs.map((d, i) => (
          <button key={d} onClick={() => setSelected(d)}
            style={{ padding: '0.4rem 1rem', borderRadius: 20, fontSize: '0.85rem', fontWeight: 600, border: '2px solid', cursor: 'pointer',
              borderColor: selected === d ? COLORS[i] : '#e2e8f0',
              background: selected === d ? COLORS[i] : '#fff',
              color: selected === d ? '#fff' : '#475569',
            }}>
            {d}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        {/* Drug info card */}
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 12 }}>Drug Information</h3>
          {infoLoading && <p style={{ color: '#64748b', fontSize: '0.84rem' }}>Loading…</p>}
          {infoError  && <ErrorAlert message={infoError} />}
          {info && !infoLoading && (
            <dl style={{ fontSize: '0.84rem' }}>
              {[
                ['Drug Name', info.drug_name],
                ['ChEMBL ID', info.chembl_id],
                ['Subjects', info.subject_count],
                ['Observations', info.observation_count],
                ['Status', info.scientific_adequacy_status],
              ].map(([k, v]) => (
                <div key={String(k)} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', padding: '0.45rem 0' }}>
                  <dt style={{ color: '#64748b', fontWeight: 500 }}>{k}</dt>
                  <dd style={{ color: '#1e293b', fontWeight: 600 }}>{String(v)}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        {/* Cluster info */}
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 12 }}>Kinetic Cluster (SVD Ward k=2)</h3>
          {selected && (() => {
            const c1 = ['cefamandole','indomethacin','remifentanil','xanomeline'];
            const isC1 = c1.includes(selected);
            return (
              <div>
                <div style={{ background: isC1 ? '#eff6ff' : '#f0fdf4', borderRadius: 8, padding: '1rem', textAlign: 'center', marginBottom: 12 }}>
                  <p style={{ fontWeight: 800, fontSize: '1.4rem', color: isC1 ? '#1d4ed8' : '#15803d' }}>
                    {isC1 ? 'Cluster 1' : 'Cluster 2'}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: 4 }}>
                    {isC1 ? 'Rapid Clearance / IV Decay' : 'Extended Elimination / Oral Dynamics'}
                  </p>
                </div>
                <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  ⚠ Cluster assignment reflects kinetic curve morphology only — not clinical drug interaction.
                </p>
              </div>
            );
          })()}
        </div>
      </div>

      {/* PK Trajectory chart */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 4 }}>
          PK Trajectory — <span style={{ color: '#2563eb' }}>{selected}</span>
        </h3>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 16 }}>
          Peak-normalized (Cmax=1) mean concentration over time. Drug-level aggregate of all subjects.
        </p>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" label={{ value: 'Time (h)', position: 'insideBottom', offset: -3 }} tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: unknown) => (v as number).toFixed(4)} />
            <Legend />
            <Line type="monotone" dataKey="Peak Norm" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
