import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  message: string;
}

const ErrorAlert: React.FC<Props> = ({ message }) => (
  <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
    <AlertTriangle className="mt-0.5 shrink-0 w-5 h-5" />
    <div>
      <p className="font-semibold text-sm">Failed to load data</p>
      <p className="text-sm mt-0.5 text-red-600">{message}</p>
      <p className="text-xs mt-1 text-red-500">Ensure the FastAPI backend is running at port 8000.</p>
    </div>
  </div>
);

export default ErrorAlert;
