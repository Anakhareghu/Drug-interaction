import React from 'react';

interface Props {
  message?: string;
}

const LoadingSpinner: React.FC<Props> = ({ message = 'Loading data…' }) => (
  <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-500">
    <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
    <p className="text-sm">{message}</p>
  </div>
);

export default LoadingSpinner;
