import React from 'react';

interface Props {
  label: string;
  value: string | number;
  sub?: string;
  colorClass?: string;
}

const StatCard: React.FC<Props> = ({ label, value, sub, colorClass = 'text-blue-600' }) => (
  <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
    <p className={`text-3xl font-extrabold ${colorClass}`}>{value}</p>
    {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
  </div>
);

export default StatCard;
