import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Siren,
  ReceiptText,
  Network,
  Search,
  FlaskConical,
  Bot,
  BarChart3,
  ShieldCheck,
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/threats', label: 'Live Threats', icon: Siren },
    { to: '/transactions', label: 'Transactions', icon: ReceiptText },
    { to: '/fraud-network', label: 'Fraud Network', icon: Network },
    { to: '/investigations', label: 'Investigations', icon: Search },
    { to: '/simulator', label: 'Risk Simulator', icon: FlaskConical },
    { to: '/assistant', label: 'AI Risk Assistant', icon: Bot },
    { to: '/analytics', label: 'Model Analytics', icon: BarChart3 },
    { to: '/audit', label: 'Audit Trail', icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Logo Section */}
        <Link to="/dashboard" className="h-16 flex items-center gap-3 px-6 border-b border-slate-800/80 hover:opacity-90 transition">
          <img src="/logo.svg" alt="BharatSHIELD" className="w-8 h-8" />
          <div>
            <div className="font-extrabold tracking-tight text-white flex items-center gap-1.5 text-base">
              Bharat<span className="text-emerald-400">SHIELD</span>
            </div>
            <div className="text-[10px] text-slate-500 font-mono uppercase tracking-wider font-semibold">
              Risk Intelligence
            </div>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/5 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`
                }
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer / System Status badge */}
      <div className="p-3 m-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>Risk Engine Online</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5">
          XGBoost + SHAP + SHA-256 Audit Chain active.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
