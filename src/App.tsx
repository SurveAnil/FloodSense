import { useEffect, useState } from 'react';
import { AppShell, type View } from './components/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { PrioritiesPage } from './pages/PrioritiesPage';
import { StatusPage } from './pages/StatusPage';
import { apiDataService } from './services/data-service';
import type { DashboardData } from './types/domain';
import './styles.css';

export default function App() {
  const [view, setView] = useState<View>('dashboard');
  const [data, setData] = useState<DashboardData>();
  useEffect(() => { apiDataService.getDashboardData().then(setData).catch((error: Error) => console.error(error)); }, []);
  useEffect(() => { const handler = () => setView('dashboard'); window.addEventListener('navigate-dashboard', handler); return () => window.removeEventListener('navigate-dashboard', handler); }, []);
  if (!data) return <div className="loading-screen">Loading FloodSense data…</div>;
  return <AppShell view={view} dataMode={data.dataMode} onNavigate={setView}>{view === 'dashboard' && <DashboardPage data={data} onPriorityView={() => setView('priorities')} />}{view === 'priorities' && <PrioritiesPage data={data} />}{view === 'status' && <StatusPage data={data} />}</AppShell>;
}
