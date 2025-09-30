import { api } from './api';

export async function getBillingStatus(): Promise<{ subscribed: boolean }> {
  return api('/billing/stripe/status');
}

export async function listStripeEvents(params: { limit?: number; after_id?: number; event_type?: string; processed?: boolean } = {}) {
  const q = new URLSearchParams();
  if (params.limit) q.set('limit', String(params.limit));
  if (params.after_id) q.set('after_id', String(params.after_id));
  if (typeof params.processed === 'boolean') q.set('processed', String(params.processed));
  if (params.event_type) q.set('event_type', params.event_type);
  return api(`/billing/stripe/events?${q.toString()}`);
}
