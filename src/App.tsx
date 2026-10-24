import { useCallback, useEffect, useState } from 'react';
import { AppShell, type View } from './components/AppShell';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { PrioritiesPage } from './pages/PrioritiesPage';
import { ReportsPage } from './pages/ReportsPage';
import { ResponseCoordinationPage } from './pages/ResponseCoordinationPage';
import { StatusPage } from './pages/StatusPage';
import { ApiError, authService, type AuthUser } from './services/auth-service';
import { apiDataService } from './services/data-service';
import type { DashboardData } from './types/domain';
import './auth.css';
import './analytics.css';
import './reports.css';
import './styles.css';
import './gis.css';
import './theme.css';

export default function App() {
  const [view, setView] = useState<View>('dashboard');
  const [data, setData] = useState<DashboardData>();
  const [user, setUser] = useState<AuthUser>();
  const [loading, setLoading] = useState(true);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [serviceError, setServiceError] = useState<string>();
  const [inspectionLocationId, setInspectionLocationId] = useState<string>();

  const loadRiskData = useCallback(async () => {
    setDashboardLoading(true);
    try {
      setData(await apiDataService.getDashboardData());
      setServiceError(undefined);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        setUser(undefined);
        setData(undefined);
      }
      setServiceError(reason instanceof Error ? reason.message : 'Risk information could not be loaded.');
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    authService.getCurrentUser()
      .then(async (current) => {
        if (!active) return;
        setUser(current);
        await loadRiskData();
      })
      .catch((reason: unknown) => {
        if (active && !(reason instanceof ApiError && reason.status === 401)) {
          setServiceError(reason instanceof Error ? reason.message : 'FloodSense authentication is unavailable.');
        }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [loadRiskData]);

  useEffect(() => {
    const handler = () => setView('dashboard');
    window.addEventListener('navigate-dashboard', handler);
    return () => window.removeEventListener('navigate-dashboard', handler);
  }, []);

  const completeSignIn = async (authenticatedUser: AuthUser) => {
    setUser(authenticatedUser);
    setServiceError(undefined);
    await loadRiskData();
  };

  const signOut = async () => {
    try {
      await authService.logout();
      setUser(undefined);
      setData(undefined);
      setView('dashboard');
      setServiceError(undefined);
    } catch (reason) {
      setServiceError(reason instanceof Error ? reason.message : 'Sign out failed.');
    }
  };

  if (loading) return <div className="loading-screen">Checking FloodSense session…</div>;
  if (!user) return <LoginPage onAuthenticated={completeSignIn} serviceError={serviceError} />;
  if (!data && dashboardLoading) return <div className="loading-screen">Loading flood-risk information…</div>;
  if (!data) return <main className="auth-page"><section className="panel auth-card">
    <div className="form-error" role="alert">{serviceError || 'Flood-risk information is unavailable.'}</div>
    <div className="auth-recovery"><button className="primary-button" type="button" onClick={loadRiskData}>Retry</button><button className="secondary-button" type="button" onClick={signOut}>Sign out</button></div>
  </section></main>;

  return <AppShell view={view} dataMode={data.dataMode} user={user} onNavigate={(next) => {
    setView(next);
    if (next !== 'field-work') setInspectionLocationId(undefined);
  }} onLogout={signOut}>
    {serviceError && <div className="app-error" role="alert">{serviceError}</div>}
    {view === 'dashboard' && <DashboardPage data={data} role={user.role} onPriorityView={() => setView('priorities')} onRefresh={loadRiskData} onInspectHotspot={user.role === 'FIELD_RESPONSE_PLANNING' ? (location) => {
      setInspectionLocationId(location.id);
      setView('field-work');
    } : undefined} />}
    {view === 'priorities' && <PrioritiesPage data={data} />}
    {view === 'analytics' && <AnalyticsPage role={user.role} />}
    {view === 'status' && <StatusPage data={data} />}
    {view === 'users' && user.role === 'DISASTER_MANAGEMENT_ADMIN' && <AdminUsersPage />}
    {view === 'reports' && user.role === 'CITIZEN' && <ReportsPage role={user.role} locations={data.locations} />}
    {view === 'field-work' && user.role === 'FIELD_RESPONSE_PLANNING' && <ReportsPage role={user.role} locations={data.locations} inspectionLocationId={inspectionLocationId} />}
    {view === 'review' && user.role === 'DISASTER_MANAGEMENT_ADMIN' && <ReportsPage role={user.role} locations={data.locations} />}
    {view === 'response-admin' && user.role === 'DISASTER_MANAGEMENT_ADMIN' && <ResponseCoordinationPage isAdmin />}
    {view === 'response-field' && user.role === 'FIELD_RESPONSE_PLANNING' && <ResponseCoordinationPage isAdmin={false} />}
  </AppShell>;
}
