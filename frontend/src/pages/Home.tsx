import { Link } from 'react-router-dom';
import { Activity, ArrowRight, Database, GitBranch, FlaskConical } from 'lucide-react';

export default function Home() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%)', borderRadius: 16, padding: '3rem 2rem', textAlign: 'center', color: '#fff', marginBottom: 32 }}>
        <Activity style={{ width: 56, height: 56, margin: '0 auto 1rem', color: '#93c5fd' }} />
        <h1 style={{ fontSize: '2rem', fontWeight: 800, lineHeight: 1.2, marginBottom: '1rem' }}>
          Drug Interaction Analysis
        </h1>
        <p style={{ fontSize: '1rem', color: '#bfdbfe', maxWidth: 560, margin: '0 auto 1.5rem', lineHeight: 1.7 }}>
          Using Pharmacokinetic Trajectories and Drug–Target Networks to evaluate
          the coupling between macroscopic PK trajectory distances and primary ChEMBL
          drug–target profile topology.
        </p>
        <Link to="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#2563eb', color: '#fff', padding: '0.6rem 1.4rem', borderRadius: 8, fontWeight: 600, fontSize: '0.9rem', textDecoration: 'none' }}>
          View Dashboard <ArrowRight style={{ width: 16, height: 16 }} />
        </Link>
      </div>

      {/* Feature cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {[
          {
            icon: <Database style={{ width: 28, height: 28, color: '#3b82f6' }} />,
            title: 'Frozen Dataset',
            body: '7 validated drugs · 452 human subjects · 5,174 macroscopic PK observations. Dose & peak normalized on a 15-point time grid.',
          },
          {
            icon: <GitBranch style={{ width: 28, height: 28, color: '#10b981' }} />,
            title: 'SVD / DMD Pipeline',
            body: 'Low-rank SVD (r=2) captures ≥93.8% variance. Discrete DMD extracts temporal dynamics. Pairwise SVD & DTW distances computed.',
          },
          {
            icon: <FlaskConical style={{ width: 28, height: 28, color: '#8b5cf6' }} />,
            title: 'ChEMBL Network',
            body: '7×196 binary drug-target matrix. 222 validated interaction edges. Jaccard & Cosine target similarity quantified.',
          },
        ].map(({ icon, title, body }) => (
          <div key={title} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
            <div style={{ marginBottom: 12 }}>{icon}</div>
            <h3 style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: 8, color: '#1e293b' }}>{title}</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.6 }}>{body}</p>
          </div>
        ))}
      </div>

      {/* Quick nav */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1.25rem 1.5rem', marginTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', marginRight: 8, alignSelf: 'center' }}>Explore →</span>
        {[['Methodology','/methodology'],['Dashboard','/dashboard'],['Drug Explorer','/explorer'],['PK Analysis','/pk-analysis'],['Network','/network'],['Results','/results']].map(([label, to]) => (
          <Link key={to} to={to} style={{ fontSize: '0.82rem', color: '#2563eb', background: '#eff6ff', padding: '0.3rem 0.75rem', borderRadius: 20, textDecoration: 'none', fontWeight: 500 }}>
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}
