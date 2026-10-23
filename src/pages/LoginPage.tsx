import { useEffect, useState, type FormEvent } from 'react';
import { authService, type AppRole, type AuthUser } from '../services/auth-service';

const demoAccounts: Array<{ role: AppRole; label: string }> = [
  { role: 'CITIZEN', label: 'Citizen' },
  { role: 'FIELD_RESPONSE_PLANNING', label: 'Field Response Planning' },
  { role: 'DISASTER_MANAGEMENT_ADMIN', label: 'Disaster Management Admin' },
];

export function LoginPage({
  onAuthenticated,
  serviceError,
}: {
  onAuthenticated: (user: AuthUser) => Promise<void>;
  serviceError?: string;
}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string>();
  const [demoError, setDemoError] = useState<string>();
  const [demoMode, setDemoMode] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    authService.getDemoMode()
      .then(setDemoMode)
      .catch((reason: unknown) => setDemoError(reason instanceof Error ? reason.message : 'Demo mode could not be checked.'));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(undefined);
    try {
      await onAuthenticated(await authService.login(email, password));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Sign-in failed.');
    } finally {
      setBusy(false);
    }
  };

  const submitDemo = async (role: AppRole) => {
    setBusy(true);
    setError(undefined);
    try {
      await onAuthenticated(await authService.loginAsDemo(role));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Demo sign-in failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="panel auth-card">
        <div className="brand-mark auth-mark">FS</div>
        <span className="eyebrow">Pune flood-risk intelligence</span>
        <h1>Sign in to FloodSense</h1>
        <p>Access risk information and operational views for your account.</p>
        {(error || serviceError || demoError) && <div className="form-error" role="alert">{error || serviceError || demoError}</div>}
        <form className="auth-form" onSubmit={submit}>
          <label>Email address<input autoComplete="username" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        </form>
        {demoMode && <section className="demo-access" aria-label="Development demo accounts">
          <strong>Development/demo accounts</strong>
          <p>Demo sign-in is enabled. These accounts use replay data and are not real users.</p>
          <div className="demo-account-list">{demoAccounts.map(({ role, label }) =>
            <button type="button" key={role} disabled={busy} onClick={() => submitDemo(role)}>{label}</button>,
          )}</div>
        </section>}
      </section>
    </main>
  );
}
