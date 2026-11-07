'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function TechPortal() {
  const [apiKey, setApiKey] = useState('');
  const [orders, setOrders] = useState<any[]>([]);

  async function load() {
    if (!apiKey) return;
    const r = await fetch(`${API}/technician/my-orders`, { headers: { Authorization: `Bearer ${apiKey}` } });
    setOrders(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function act(orderId: string, path: string, body?: any) {
    await fetch(`${API}/technician/orders/${orderId}/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify(body || {}),
    });
    load();
  }

  return (
    <div>
      <h1>Technician Portal</h1>
      <p style={{ color: 'var(--muted)' }}>Only assigned orders appear. Start → Complete with report.</p>
      <input placeholder="Technician access token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <button onClick={load} style={{ marginBottom: 16 }}>Reload my orders</button>
      {orders.map((o) => (
        <div key={o.id} className="card" style={{ marginBottom: 12 }}>
          <h3>Order {String(o.id).slice(0, 8)} — {o.status}</h3>
          <p style={{ fontSize: 13 }}>{(o.timeline || []).map((s: any, i: number) => <span key={i}>• {s.status} </span>)}</p>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => act(o.id, 'start')}>Start</button>
            <button onClick={() => { const r = prompt('Completion report:'); if (r) act(o.id, 'complete', { report: r }); }}>Complete</button>
          </div>
        </div>
      ))}
    </div>
  );
}
