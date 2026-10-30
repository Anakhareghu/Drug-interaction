import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  Activity, Home, BookOpen, LayoutDashboard, FlaskConical, 
  TrendingUp, Network, BarChart3, LogOut, LogIn, UserCheck 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const links = [
  { to: '/',            label: 'Home',              icon: Home },
  { to: '/methodology', label: 'Methodology',       icon: BookOpen },
  { to: '/dashboard',   label: 'Dashboard',         icon: LayoutDashboard },
  { to: '/explorer',    label: 'Drug Explorer',     icon: FlaskConical },
  { to: '/pk-analysis', label: 'PK Analysis',       icon: TrendingUp },
  { to: '/network',     label: 'Network Analysis',  icon: Network },
  { to: '/results',     label: 'Integrated Results',icon: BarChart3 },
];

const Sidebar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside className="w-60 shrink-0 bg-slate-900 text-white flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-700">
        <Activity className="w-6 h-6 text-blue-400" />
        <span className="font-bold text-sm leading-tight">Drug Interaction<br/>Analysis</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-blue-700 text-white font-semibold'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Auth Status & User Box */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60">
        {isAuthenticated && user ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-slate-800/80 border border-slate-700/50">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="overflow-hidden flex-1">
                <p className="text-xs font-semibold text-white truncate">{user.username}</p>
                <p className="text-[10px] text-slate-400 truncate">{user.role}</p>
              </div>
            </div>
            <button
              id="logout-btn"
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-950/60 hover:bg-rose-900 text-rose-200 border border-rose-800/60 transition"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        ) : (
          <NavLink
            to="/login"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm"
          >
            <LogIn className="w-3.5 h-3.5" />
            Sign In
          </NavLink>
        )}
      </div>

      {/* Footer tag */}
      <div className="px-5 py-2.5 text-[11px] text-slate-500 border-t border-slate-800 flex items-center justify-between">
        <span>Phase 6C Auth</span>
        <span className="text-emerald-400 font-mono">JWT / HS256</span>
      </div>
    </aside>
  );
};

export default Sidebar;
