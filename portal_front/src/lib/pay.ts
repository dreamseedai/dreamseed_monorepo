import { api } from './api';

export async function startCheckout(): Promise<void> {
  const res = await api('/billing/stripe/create-checkout-session', {
    method: 'POST',
    body: JSON.stringify({}),
  });
  if ((res as any)?.url) {
    window.location.href = (res as any).url as string;
    return;
  }
  if ((res as any)?.id) {
    window.location.href = `https://checkout.stripe.com/pay/${(res as any).id}`;
    return;
  }
  throw new Error('No checkout session');
}

export async function manageSubscription(): Promise<void> {
  const res = await api('/billing/stripe/portal', { method: 'POST', body: JSON.stringify({}) });
  if ((res as any)?.url) {
    window.location.href = (res as any).url as string;
    return;
  }
  throw new Error('No portal url');
}


