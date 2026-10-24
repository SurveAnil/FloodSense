export type AppRole = 'CITIZEN' | 'FIELD_RESPONSE_PLANNING' | 'DISASTER_MANAGEMENT_ADMIN';

export interface AuthUser {
  id: string;
  email: string;
  role: AppRole;
  is_demo: boolean;
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export function resolveApiBaseUrl(configuredUrl: string | undefined, isDevelopment: boolean): string {
  return (configuredUrl?.trim() || (isDevelopment ? 'http://localhost:8000' : '')).replace(/\/$/, '');
}

export const apiBaseUrl = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL, import.meta.env.DEV);

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = 'The FloodSense service could not complete the request.';
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the generic service error when the response has no JSON body.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const authService = {
  async getCurrentUser() {
    return parseResponse<AuthUser>(await fetch(`${apiBaseUrl}/api/auth/me`, { credentials: 'include' }));
  },
  async login(email: string, password: string) {
    return parseResponse<AuthUser>(await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }));
  },
  async getDemoMode() {
    const health = await parseResponse<{ demo_mode: string }>(
      await fetch(`${apiBaseUrl}/health`, { credentials: 'include' }),
    );
    return health.demo_mode === 'true';
  },
  async loginAsDemo(role: AppRole) {
    return parseResponse<AuthUser>(await fetch(`${apiBaseUrl}/api/auth/demo-login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    }));
  },
  async logout() {
    return parseResponse<void>(await fetch(`${apiBaseUrl}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }));
  },
  async createUser(email: string, password: string, role: AppRole) {
    return parseResponse<AuthUser>(await fetch(`${apiBaseUrl}/api/admin/users`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role }),
    }));
  },
};
