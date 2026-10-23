import { useState, type FormEvent } from 'react';
import { authService, type AppRole } from '../services/auth-service';

const roleLabels: Record<AppRole, string> = {
  CITIZEN: 'Citizen',
  FIELD_RESPONSE_PLANNING: 'Field Response Planning',
  DISASTER_MANAGEMENT_ADMIN: 'Disaster Management Admin',
};

export function AdminUsersPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<AppRole>('CITIZEN');
  const [message, setMessage] = useState<string>();
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setMessage(undefined);
    setError(undefined);
    try {
      const created = await authService.createUser(email, password, role);
      setEmail('');
      setPassword('');
      setMessage(`Created ${created.email} with the ${roleLabels[created.role]} role.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Account creation failed.');
    } finally {
      setBusy(false);
    }
  };

  return <div className="page">
    <div className="page-heading"><div><span className="eyebrow">Access management</span><h1>Create an account</h1><p>Assign one of the three FloodSense roles to a new account.</p></div></div>
    <section className="panel admin-form-panel">
      <form className="auth-form" onSubmit={submit}>
        <label>Email address<input type="email" autoComplete="off" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Initial password<input type="password" autoComplete="new-password" minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} required /><small>Use at least 12 characters.</small></label>
        <label>Account role<select value={role} onChange={(event) => setRole(event.target.value as AppRole)}>{Object.entries(roleLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        {error && <div className="form-error" role="alert">{error}</div>}
        {message && <div className="form-success" role="status">{message}</div>}
        <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
      </form>
    </section>
  </div>;
}
