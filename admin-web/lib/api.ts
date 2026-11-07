/**
 * API client — server-side auth only. Token stored in httpOnly cookie via server route
 * (see app/api/session). Never expose admin secrets to the client.
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export interface Overview {
  range: string;
  total_customers: number;
  new_customers: number;
  registered_devices: number;
  active_technicians: number;
  total_orders: number;
  completed_orders: number;
  failed_orders: number;
  gross_revenue_cents: number;
  refunds_cents: number;
  net_revenue_cents: number;
  active_sessions: number;
}

export const api = {
  overview: (range = '7d') => req<Overview>(`/admin/overview?range=${range}`),
  health: () => req<{ status: string; db: boolean }>('/health'),
};
