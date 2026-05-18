import { Activity, ChefHat, ClipboardList, FileText, LogOut, Users } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

function NavItem({ to, icon: Icon, label, badge }: { to: string; icon: typeof Users; label: string; badge?: string }) {
  const { pathname } = useLocation();
  const active = pathname === to || pathname.startsWith(to + '/') || (to === '/patients' && pathname === '/patients');
  return (
    <Link to={to} className={active ? 'active' : ''}>
      <Icon size={16} />
      {label}
      {badge && <span className="nav-badge">{badge}</span>}
    </Link>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  const doctor = useAuthStore((s) => s.doctor);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="layout-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <strong>NutriPlan AI</strong>
          <span>Clinical</span>
        </div>

        <div className="sidebar-section">Workspace</div>
        <NavItem to="/patients"  icon={Users}         label="Patients" />
        <NavItem to="/plans"     icon={ClipboardList} label="Diet Plans" />
        <NavItem to="/recipes"   icon={ChefHat}       label="Custom Recipes" badge="Soon" />
        <NavItem to="/documents" icon={FileText}       label="Documents" badge="Soon" />
        <NavItem to="/audit"     icon={Activity}       label="Audit Log" />

        <div className="sidebar-footer">
          <div style={{ padding: '0 4px 10px', fontSize: 13, color: 'rgba(148,163,184,0.7)' }}>
            {doctor?.name && <div style={{ color: '#e2e8f0', fontWeight: 600, marginBottom: 2 }}>{doctor.name}</div>}
            {doctor?.clinic && <div>{doctor.clinic}</div>}
          </div>
          <button
            className="button-ghost"
            style={{ width: '100%', justifyContent: 'flex-start', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: '#94a3b8' }}
            onClick={() => void logout()}
          >
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </aside>

      <section className="layout-main">
        {children}
      </section>
    </div>
  );
}
