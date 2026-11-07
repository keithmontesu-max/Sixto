'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ServicesAdminPage() {
  const [apiKey, setApiKey] = useState('');
  const [services, setServices] = useState<any[]>([]);
  const [coupons, setCoupons] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const [form, setForm] = useState({ name: '', slug: '', price_cents: '0', currency: 'PHP', category: 'ROOT', eta_minutes: '60', refund_policy: 'Refund per Terms of Service' });
  const [coupon, setCoupon] = useState({ code: '', discount_percent: '10', discount_cents: '0', max_uses: '0' });

  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([
        fetch(`${API}/services/admin/all`, { headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {} }),
        fetch(`${API}/coupons/admin/all`, { headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {} }),
      ]);
      setServices(await s.json());
      setCoupons(await c.json());
    } catch (e: any) {
      setMsg(e.message);
    }
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function saveService(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${API}/services/admin/upsert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) },
      body: JSON.stringify({ ...form, price_cents: Number(form.price_cents), eta_minutes: Number(form.eta_minutes), description: form.name, is_active: true, requires_root_eligible: true, terms: '' }),
    });
    setMsg(res.ok ? 'Service saved' : await res.text());
    load();
  }

  async function saveCoupon(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${API}/coupons/admin/upsert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) },
      body: JSON.stringify({ ...coupon, discount_percent: Number(coupon.discount_percent), discount_cents: Number(coupon.discount_cents), max_uses: Number(coupon.max_uses), is_active: true }),
    });
    setMsg(res.ok ? 'Coupon saved' : await res.text());
    load();
  }

  return (
    <div>
      <h1>Services & Pricing</h1>
      <p style={{ color: 'var(--muted)' }}>Central pricing. Prices never live in the APK — customers always fetch from here.</p>
      <input placeholder="Admin access token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      {msg && <p>{msg}</p>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <form onSubmit={saveService}>
          <h3>New / edit service</h3>
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required style={{ width: '100%' }} /><br />
          <input placeholder="Slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required style={{ width: '100%' }} /><br />
          <input placeholder="Price cents" value={form.price_cents} onChange={(e) => setForm({ ...form, price_cents: e.target.value })} style={{ width: '100%' }} /><br />
          <button type="submit">Save service</button>
          <table style={{ marginTop: 16 }}>
            <tbody>{services.map((s) => <tr key={s.id}><td>{s.name}</td><td>{s.price_cents}</td><td>{s.is_active ? 'active' : 'off'}</td></tr>)}</tbody>
          </table>
        </form>
        <form onSubmit={saveCoupon}>
          <h3>New / edit coupon</h3>
          <input placeholder="Code" value={coupon.code} onChange={(e) => setCoupon({ ...coupon, code: e.target.value })} required style={{ width: '100%' }} /><br />
          <input placeholder="Percent 0-100" value={coupon.discount_percent} onChange={(e) => setCoupon({ ...coupon, discount_percent: e.target.value })} style={{ width: '100%' }} /><br />
          <input placeholder="Fixed cents (overrides %)" value={coupon.discount_cents} onChange={(e) => setCoupon({ ...coupon, discount_cents: e.target.value })} style={{ width: '100%' }} /><br />
          <button type="submit">Save coupon</button>
          <table style={{ marginTop: 16 }}>
            <tbody>{coupons.map((c) => <tr key={c.id}><td>{c.code}</td><td>{c.discount_percent}% / {c.discount_cents}¢</td><td>{c.used_count}/{c.max_uses || '∞'}</td></tr>)}</tbody>
          </table>
        </form>
      </div>
    </div>
  );
}
