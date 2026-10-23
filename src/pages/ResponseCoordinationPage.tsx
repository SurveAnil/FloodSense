import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  reportService,
  type FieldResponseUser,
  type FloodProblem,
  type ResponseTask,
  type ResponseTaskStatus,
} from '../services/report-service';
import { ApiError } from '../services/auth-service';

const statusFlow: Record<string, ResponseTaskStatus | undefined> = {
  ASSIGNED: 'ACCEPTED',
  ACCEPTED: 'EN_ROUTE',
  EN_ROUTE: 'INSPECTED',
  INSPECTED: 'ACTION_REQUIRED',
  ACTION_REQUIRED: 'RESOLVED',
};
const statusLabel = (value: string) => value.replace(/_/g, ' ');
const valueOf = (form: HTMLFormElement, field: string) => String(new FormData(form).get(field) ?? '');

export function ResponseCoordinationPage({ isAdmin }: { isAdmin: boolean }) {
  const [tasks, setTasks] = useState<ResponseTask[]>([]);
  const [problems, setProblems] = useState<FloodProblem[]>([]);
  const [fieldUsers, setFieldUsers] = useState<FieldResponseUser[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();

  const reload = useCallback(async () => {
    setError(undefined);
    try {
      if (isAdmin) {
        const [taskList, problemList, users] = await Promise.all([
          reportService.adminTasks(),
          reportService.floodProblems(),
          reportService.fieldUsers(),
        ]);
        setTasks(taskList);
        setProblems(problemList);
        setFieldUsers(users);
      } else {
        setTasks(await reportService.fieldTasks());
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Response coordination data could not be loaded.');
    }
  }, [isAdmin]);

  useEffect(() => { void reload(); }, [reload]);

  const run = async (operation: () => Promise<unknown>, message: string) => {
    setBusy(true);
    setError(undefined);
    setNotice(undefined);
    try {
      await operation();
      setNotice(message);
      await reload();
      return true;
    } catch (reason) {
      setError(reason instanceof ApiError || reason instanceof Error
        ? reason.message
        : 'The response action could not be completed.');
      return false;
    } finally {
      setBusy(false);
    }
  };

  const createTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const deadline = valueOf(form, 'due_at');
    void run(() => reportService.createTask({
      flood_problem_id: valueOf(form, 'flood_problem_id'),
      instruction: valueOf(form, 'instruction'),
      details: valueOf(form, 'details'),
      priority: valueOf(form, 'priority') as ResponseTask['priority'],
      assigned_user_id: valueOf(form, 'assigned_user_id'),
      due_at: deadline ? new Date(deadline).toISOString() : undefined,
    }), 'Response task assigned to Field Response & Planning.').then((success) => { if (success) form.reset(); });
  };

  const updateTask = (task: ResponseTask, event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const next = statusFlow[task.status];
    if (!next) return;
    void run(async () => reportService.updateTask(task.id, {
      new_status: next,
      action_taken: valueOf(form, 'action_taken'),
      condition: valueOf(form, 'condition'),
      internal_notes: valueOf(form, 'internal_notes'),
      blockers: valueOf(form, 'blockers'),
      evidence: await reportService.encodeFiles(form.querySelector<HTMLInputElement>('input[type="file"]')?.files ?? null),
    }), `Task progress submitted: ${statusLabel(next).toLowerCase()}.`).then((success) => { if (success) form.reset(); });
  };

  const tasksByProblem = new Map<string, ResponseTask[]>();
  for (const task of tasks) {
    const group = tasksByProblem.get(task.flood_problem_id) ?? [];
    group.push(task);
    tasksByProblem.set(task.flood_problem_id, group);
  }

  return <div className="page response-page">
    <div className="page-heading">
      <div>
        <span className="eyebrow">Phase 3 · Response coordination</span>
        <h1>{isAdmin ? 'Response instructions & monitoring' : 'Assigned response tasks'}</h1>
        <p>{isAdmin
          ? 'Issue operational instructions only for approved FloodProblems and monitor field completion.'
          : 'Advance assigned work through its response lifecycle and submit findings for administrator review.'}</p>
      </div>
      <button type="button" className="secondary-button" onClick={() => void reload()} disabled={busy}>Refresh</button>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {notice && <div className="form-success" role="status">{notice}</div>}

    {isAdmin && <section className="panel response-form-panel">
      <h2>Create response instruction</h2>
      <p>Only approved official FloodProblems can receive a response task.</p>
      <form className="auth-form response-form" onSubmit={createTask}>
        <label>Approved FloodProblem
          <select name="flood_problem_id" defaultValue="" required>
            <option value="" disabled>Select an official problem</option>
            {problems.map((problem) => <option key={problem.id} value={problem.id}>
              {problem.severity} · {problem.id} · {problem.status}
            </option>)}
          </select>
        </label>
        <label>Assign to Field Response user
          <select name="assigned_user_id" defaultValue="" required>
            <option value="" disabled>Select a field user</option>
            {fieldUsers.map((user) => <option key={user.id} value={user.id}>{user.email}</option>)}
          </select>
        </label>
        <label>Priority<select name="priority" defaultValue="NORMAL">
          <option value="LOW">Low</option><option value="NORMAL">Normal</option>
          <option value="HIGH">High</option><option value="URGENT">Urgent</option>
        </select></label>
        <label>Instruction<input name="instruction" minLength={3} maxLength={500} required placeholder="Inspect and clear the affected drainage channel" /></label>
        <label>Task details<textarea name="details" maxLength={2000} rows={3} placeholder="Operational context and expected action." /></label>
        <label>Deadline (optional)<input name="due_at" type="datetime-local" /></label>
        <button className="primary-button" type="submit" disabled={busy || problems.length === 0 || fieldUsers.length === 0}>Assign response task</button>
      </form>
      {problems.length === 0 && <p className="report-muted">No approved FloodProblems are available for assignment.</p>}
      {fieldUsers.length === 0 && <p className="report-muted">No active Field Response users are available.</p>}
    </section>}

    {tasks.length === 0 ? <section className="panel report-empty">
      {isAdmin ? 'No response tasks have been issued.' : 'No response tasks are assigned to your account.'}
    </section> : <section className="response-task-list">
      {tasks.map((task) => <article className="panel response-task-card" key={task.id}>
        <div className="report-card-heading">
          <div><span className="eyebrow">{task.priority} · FloodProblem {task.flood_problem_id}</span><h2>{task.instruction}</h2></div>
          <span className={`report-status status-${task.status.toLowerCase().replace(/_/g, '-')}`}>{statusLabel(task.status)}</span>
        </div>
        {task.details && <p>{task.details}</p>}
        <p className="report-muted">
          Assigned to {isAdmin ? task.assigned_user_email : 'you'}
          {task.due_at ? ` · Due ${new Date(task.due_at).toLocaleString()}` : ''}
        </p>
        {task.completion_status === 'PENDING_REVIEW' && <p className="official-problem-note">Field completion is awaiting administrator review.</p>}
        {task.completion_status === 'APPROVED' && <p className="official-problem-note">Completion approved by an administrator.</p>}

        {task.updates.length > 0 && <details className="response-history">
          <summary>Operational history ({task.updates.length})</summary>
          {task.updates.map((update) => <div className="report-history" key={update.id}>
            <strong>{statusLabel(update.previous_status)} → {statusLabel(update.new_status)} · {new Date(update.created_at).toLocaleString()}</strong>
            {update.action_taken && <span><b>Action:</b> {update.action_taken}</span>}
            {update.condition && <span><b>Condition:</b> {update.condition}</span>}
            {update.internal_notes && <span><b>Internal notes:</b> {update.internal_notes}</span>}
            {update.blockers && <span><b>Blockers:</b> {update.blockers}</span>}
            {update.completion_decision && <span><b>Completion review:</b> {statusLabel(update.completion_decision)}</span>}
            {update.evidence.length > 0 && <ul className="evidence-list">{update.evidence.map((file) =>
              <li key={file.id}><a href={reportService.evidenceUrl(file)} target="_blank" rel="noreferrer">{file.file_name}</a></li>,
            )}</ul>}
          </div>)}
        </details>}

        {!isAdmin && statusFlow[task.status] && task.completion_status !== 'PENDING_REVIEW' && <form className="auth-form task-update-form" onSubmit={(event) => updateTask(task, event)}>
          <h3>Submit update · {statusLabel(statusFlow[task.status]!)}</h3>
          <label>Action taken / report<input name="action_taken" minLength={3} maxLength={2000} required /></label>
          <label>Inspection findings<textarea name="condition" maxLength={1000} rows={2} /></label>
          <label>Internal notes<textarea name="internal_notes" maxLength={2000} rows={2} /></label>
          <label>Blockers<textarea name="blockers" maxLength={1000} rows={2} /></label>
          <label>Resolution evidence<input name="evidence" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /><small>Up to 3 JPEG, PNG, WebP, or PDF files; 5 MB each.</small></label>
          <button className="primary-button" type="submit" disabled={busy}>Submit task update</button>
        </form>}

        {isAdmin && task.completion_status === 'PENDING_REVIEW' && <div className="review-controls">
          <button type="button" className="primary-button" disabled={busy} onClick={() => void run(
            () => reportService.reviewTaskCompletion(task.id, { decision: 'APPROVE', internal_notes: '' }),
            'Field completion approved.',
          )}>Approve completion</button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(
            () => reportService.reviewTaskCompletion(task.id, { decision: 'RETURN_FOR_ACTION', internal_notes: 'Additional action is required.' }),
            'Completion returned for further action.',
          )}>Return for further action</button>
        </div>}
      </article>)}
    </section>}

    {isAdmin && problems.map((problem) => {
      const linked = tasksByProblem.get(problem.id) ?? [];
      return linked.length > 0 ? null : <p className="report-muted" key={problem.id}>
        Approved FloodProblem {problem.id} has no response task yet.
      </p>;
    })}
  </div>;
}
