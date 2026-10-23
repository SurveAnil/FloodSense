import { Activity, ClipboardCheck, CloudRain, Database, FileText, LayoutDashboard, LogOut, Map, Menu, ShieldCheck, Users, X } from 'lucide-react';
import { useState } from 'react';
import type { AuthUser, AppRole } from '../services/auth-service';

export type View = 'dashboard' | 'priorities' | 'status' | 'analytics' | 'users' | 'reports' | 'field-work' | 'review' | 'response-admin' | 'response-field';

interface Props {
  view: View;
  dataMode: 'replay' | 'live' | 'unknown';
  user: AuthUser;
  onNavigate: (view: View) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

const roleLabels: Record<AppRole, string> = {
  CITIZEN: 'Citizen',
  FIELD_RESPONSE_PLANNING: 'Field Response Planning',
  DISASTER_MANAGEMENT_ADMIN: 'Disaster Management Admin',
};

export function AppShell({ view, dataMode, user, onNavigate, onLogout, children }: Props) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems: Array<{ id: View; label: string; Icon: typeof LayoutDashboard }> = [
    { id: 'dashboard' as const, label: 'Risk dashboard', Icon: LayoutDashboard },
    { id: 'priorities' as const, label: 'Priority hotspots', Icon: Map },
    { id: 'analytics' as const, label: 'Risk history', Icon: Activity },
    ...(user.role !== 'CITIZEN' ? [{ id: 'status' as const, label: 'Data status', Icon: Database }] : []),
    ...(user.role === 'CITIZEN' ? [{ id: 'reports' as const, label: 'My reports', Icon: FileText }] : []),
    ...(user.role === 'FIELD_RESPONSE_PLANNING' ? [{ id: 'field-work' as const, label: 'Field verification', Icon: ClipboardCheck }] : []),
    ...(user.role === 'FIELD_RESPONSE_PLANNING' ? [{ id: 'response-field' as const, label: 'Assigned response tasks', Icon: ClipboardCheck }] : []),
    ...(user.role === 'DISASTER_MANAGEMENT_ADMIN' ? [{ id: 'review' as const, label: 'Report review', Icon: ClipboardCheck }] : []),
    ...(user.role === 'DISASTER_MANAGEMENT_ADMIN' ? [{ id: 'response-admin' as const, label: 'Response coordination', Icon: ClipboardCheck }] : []),
    ...(user.role === 'DISASTER_MANAGEMENT_ADMIN' ? [{ id: 'users' as const, label: 'User access', Icon: Users }] : []),
  ];

  const navigate = (next: View) => {
    onNavigate(next);
    setMobileOpen(false);
  };

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark"><CloudRain size={20} /></div>
          <div><div className="brand-name">FloodSense</div><div className="brand-subtitle">Pune flood-risk intelligence</div></div>
        </div>
        <div className="header-context">
          <span className="demo-pill"><span className="demo-dot" />{dataMode === 'replay' ? 'Replay data' : dataMode === 'live' ? 'Live data' : 'Data mode unknown'}</span>
          {user.is_demo && <span className="account-mode-pill">Demo account</span>}
          <span className="header-user"><ShieldCheck size={16} /><span>{roleLabels[user.role]}</span></span>
          <button className="logout-button" type="button" onClick={onLogout} aria-label="Sign out"><LogOut size={16} /> <span>Sign out</span></button>
          <button className="mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle navigation">
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>
      <div className="app-body">
        <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
          <div className="sidebar-label">Decision workspace</div>
          <nav aria-label="Primary navigation">
            {navItems.map(({ id, label, Icon }) => (
              <button key={id} className={`nav-item ${view === id ? 'nav-item-active' : ''}`} onClick={() => navigate(id)}>
                <Icon size={18} /> <span>{label}</span>
              </button>
            ))}
          </nav>
          <div className="sidebar-note">
            <div className="note-title">Model output, not an official warning</div>
            <div>Use risk states to prioritize human attention. Risk outputs are not official warnings.</div>
          </div>
        </aside>
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
