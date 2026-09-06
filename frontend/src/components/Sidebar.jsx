import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ReceiptText,
  AlertTriangle,
  BarChart3,
  Bot,
  ShieldCheck,
  Zap,
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/transactions', label: 'Transactions', icon: ReceiptText },
    { to: '/alerts', label: 'Spike Alerts', icon: AlertTriangle },
    { to: '/analytics', label: 'Model Analytics', icon: BarChart3 },
    { to: '/assistant', label: 'AI Risk Assistant', icon: Bot },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Logo Section */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800/80">
          <img src="/logo.svg" alt="BharatSHIELD" className="w-8 h-8" />
          <div>
            <div className="font-extrabold tracking-tight text-white flex items-center gap-1.5 text-base">
              Bharat<span className="text-emerald-400">SHIELD</span>
            </div>
            <div className="text-[10px] text-slate-500 font-mono uppercase tracking-wider font-semibold">
              Risk Intelligence
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/5'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer / System Status badge */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>Risk Engine Active</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          XGBoost + SHAP TreeExplainer online. Sub-50ms inference.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
