import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, ShieldCheck, Lock, User, AlertCircle, CheckCircle2, Info } from 'lucide-react';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, sessionExpiredMessage, clearSessionMessage } = useAuth();

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Determine redirect target after successful login
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  // If already logged in, redirect right away
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setError(null);
    clearSessionMessage();
    setIsSubmitting(true);

    try {
      await login({ username: username.trim(), password });
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials provided.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 py-12">
      <div className="max-w-md w-full space-y-8 bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-2xl">
        {/* Header & Logo */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30 mb-4 shadow-inner">
            <Activity className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Drug Interaction Analysis
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Pharmacokinetic Trajectories & Drug–Target Networks
          </p>
          <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Phase 6C Secure Authentication
          </div>
        </div>

        {/* Session Expired Alert */}
        {sessionExpiredMessage && (
          <div className="bg-amber-950/50 border border-amber-800/80 rounded-lg p-3 text-amber-200 text-sm flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Session Notice: </span>
              {sessionExpiredMessage}
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-950/60 border border-rose-800/80 rounded-lg p-3 text-rose-200 text-sm flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Authentication Error: </span>
              {error}
            </div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <User className="w-4 h-4" />
              </div>
              <input
                id="username-input"
                type="text"
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800/90 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="password-input"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800/90 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
              />
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-semibold text-sm shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Sign In to Platform</span>
            )}
          </button>
        </form>

        {/* Demo Credentials Helper Box */}
        <div className="mt-6 p-4 rounded-xl bg-slate-800/60 border border-slate-700/70 text-xs text-slate-300 space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-slate-200">
            <Info className="w-4 h-4 text-blue-400" />
            <span>Default Test Credentials</span>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 block">Username:</span>
              <span className="text-blue-300 font-semibold">admin</span>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 block">Password:</span>
              <span className="text-emerald-300 font-semibold">admin123</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            Role: Lead Pharmacologist (Full research pipeline access)
          </p>
        </div>

        {/* Back Link */}
        <div className="text-center pt-2">
          <Link to="/" className="text-xs text-blue-400 hover:text-blue-300 transition underline underline-offset-4">
            ← Return to Public Project Overview
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
