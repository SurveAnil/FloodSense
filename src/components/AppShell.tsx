import { CloudRain, Database, LayoutDashboard, Map, Menu, ShieldCheck, X } from 'lucide-react';
import { useState } from 'react';

export type View = 'dashboard' | 'priorities' | 'status';

interface Props {
  view: View;
  dataMode: 'replay' | 'live' | 'unknown';
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

export function AppShell({ view, dataMode, onNavigate, children }: Props) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems = [
    { id: 'dashboard' as const, label: 'Risk dashboard', Icon: LayoutDashboard },
    { id: 'priorities' as const, label: 'Priority hotspots', Icon: Map },
    { id: 'status' as const, label: 'Data status', Icon: Database },
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
          <span className="header-location"><ShieldCheck size={16} /> Pune, Maharashtra</span>
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
