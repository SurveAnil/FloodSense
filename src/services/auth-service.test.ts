import { describe, expect, it } from 'vitest';
import { resolveApiBaseUrl } from './auth-service';

describe('resolveApiBaseUrl', () => {
  it('uses localhost for local development when no override is set', () => {
    expect(resolveApiBaseUrl(undefined, true)).toBe('http://localhost:8000');
  });

  it('uses a relative API path in production when the Vercel proxy is configured', () => {
    expect(resolveApiBaseUrl(undefined, false)).toBe('');
  });

  it('normalizes an explicitly configured API URL', () => {
    expect(resolveApiBaseUrl(' https://api.example.com/ ', false)).toBe('https://api.example.com');
  });
});
