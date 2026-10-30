import { useEffect, useState } from 'react';
import { getNetwork } from '../services/api';
import type { NetworkData } from '../types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

// Drug → colour mapping
const DRUG_COLORS: Record<string, string> = {
  cefamandole:   '#2563eb',
  indomethacin:  '#dc2626',
  phenobarbital: '#16a34a',
  quinidine:     '#d97706',
  remifentanil:  '#7c3aed',
  theophylline:  '#0891b2',
  xanomeline:    '#db2777',
};

const JACCARD: Record<string, Record<string, number>> = {
  cefamandole:   { cefamandole:1.000, indomethacin:0.000, phenobarbital:0.000, quinidine:0.000, remifentanil:0.000, theophylline:0.013, xanomeline:0.000 },
  indomethacin:  { cefamandole:0.000, indomethacin:1.000, phenobarbital:0.000, quinidine:0.018, remifentanil:0.000, theophylline:0.024, xanomeline:0.000 },
  phenobarbital: { cefamandole:0.000, indomethacin:0.000, phenobarbital:1.000, quinidine:0.000, remifentanil:0.000, theophylline:0.000, xanomeline:0.000 },
  quinidine:     { cefamandole:0.000, indomethacin:0.018, phenobarbital:0.000, quinidine:1.000, remifentanil:0.000, theophylline:0.179, xanomeline:0.012 },
  remifentanil:  { cefamandole:0.000, indomethacin:0.000, phenobarbital:0.000, quinidine:0.000, remifentanil:1.000, theophylline:0.000, xanomeline:0.000 },
  theophylline:  { cefamandole:0.013, indomethacin:0.024, phenobarbital:0.000, quinidine:0.179, remifentanil:0.000, theophylline:1.000, xanomeline:0.000 },
  xanomeline:    { cefamandole:0.000, indomethacin:0.000, phenobarbital:0.000, quinidine:0.012, remifentanil:0.000, theophylline:0.000, xanomeline:1.000 },
};

const DRUGS = Object.keys(JACCARD);

export default function NetworkAnalysis() {
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNetwork()
      .then(d => { setNetwork(d); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <LoadingSpinner message="Loading network data…" />;
  if (error)   return <ErrorAlert message={error} />;

  // Compute per-drug target counts from live edge data
  const targetCounts: Record<string, number> = {};
  network!.edges.forEach(e => {
    targetCounts[e.drug_name] = (targetCounts[e.drug_name] ?? 0) + 1;
  });
  const totalEdges  = network!.edges.length;
  const uniqueTargets = new Set(network!.edges.map(e => e.target_id)).size;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Network Analysis</h1>
      <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: 24 }}>
        ChEMBL drug–target bipartite interaction network and pairwise target profile similarity.
      </p>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total Drugs',      value: 7,            color: '#2563eb' },
          { label: 'Unique Targets',   value: uniqueTargets, color: '#16a34a' },
          { label: 'Interaction Edges',value: totalEdges,   color: '#d97706' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.1rem 1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
            <p style={{ fontSize: '2rem', fontWeight: 800, color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Per-drug target degree */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem 1.5rem', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 12 }}>Target Degree per Drug</h3>
        {DRUGS.map(drug => {
          const count = targetCounts[drug] ?? 0;
          const maxCount = Math.max(...Object.values(targetCounts));
          const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
          return (
            <div key={drug} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1e293b' }}>{drug}</span>
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>{count} targets</span>
              </div>
              <div style={{ background: '#f1f5f9', borderRadius: 4, height: 8, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: DRUG_COLORS[drug] ?? '#2563eb', borderRadius: 4, transition: 'width 0.4s' }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Jaccard similarity heatmap */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem 1.5rem', marginBottom: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', marginBottom: 4 }}>Pairwise Jaccard Target Similarity</h3>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: 12 }}>
          Source: Phase 5C.2 validated ChEMBL matrix. Low similarity reflects mechanistic specificity of diverse pharmacological classes.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ fontSize: '0.78rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.4rem 0.6rem', color: '#94a3b8', minWidth: 90 }}></th>
                {DRUGS.map(d => (
                  <th key={d} style={{ padding: '0.4rem 0.6rem', color: '#64748b', fontWeight: 600, textAlign: 'center', minWidth: 80, fontSize: '0.72rem' }}>
                    {d.slice(0, 7)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DRUGS.map(rowDrug => (
                <tr key={rowDrug}>
                  <td style={{ padding: '0.4rem 0.6rem', fontWeight: 600, color: '#475569', fontSize: '0.78rem' }}>{rowDrug.slice(0, 9)}</td>
                  {DRUGS.map(colDrug => {
                    const v = JACCARD[rowDrug]?.[colDrug] ?? 0;
                    const isDiag = rowDrug === colDrug;
                    return (
                      <td key={colDrug} style={{
                        padding: '0.4rem 0.6rem', textAlign: 'center', fontWeight: isDiag ? 700 : 400,
                        background: isDiag ? '#1e40af' : `rgba(37,99,235,${v * 3})`,
                        color: isDiag ? '#fff' : v > 0.1 ? '#1e3a5f' : '#475569',
                        borderRadius: 4,
                      }}>
                        {v.toFixed(3)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interpretation note */}
      <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 10, padding: '1rem 1.25rem', fontSize: '0.83rem', color: '#78350f' }}>
        <strong>Interpretation boundary:</strong> Target profile similarity reflects shared receptor/enzyme binding only.
        It does NOT constitute confirmed drug–drug interaction (DDI) or clinical synergy/antagonism.
        All results are reported as a methodological pilot on N=7 diverse drugs.
      </div>
    </div>
  );
}
