'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function OrdersAdminPage() {
  const [apiKey, setApiKey] = useState('');
  const [orders, setOrders] = useState<any[]>([]);
  const [pending, setPending] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);

  const load = useCallback(async () => {
    if (!apiKey) return;
    const [o, p] = await Promise.all([
      fetch(`${API}/admin/orders?limit=100`, { headers: { Authorization: `Bearer ${apiKey}` } }),
      fetch(`${API}/admin/payments/pending`, { headers: { Authorization: `Bearer ${apiKey}` } }),
    ]);
    setOrders(await o.json());
    setPending(await p.json());
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function confirm(pid: string) {
    await fetch(`${API}/payments/admin/${pid}/confirm`, { method: 'POST', headers: { Authorization: `Bearer ${apiKey}` } });
    load();
  }
  async function reject(pid: string) {
    await fetch(`${API}/payments/admin/${pid}/reject`, { method: 'POST', headers: { Authorization: `Bearer ${apiKey}` } });
    load();
  }

  return (
    <div>
      <h1>Orders & Pending Payments</h1>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <h3>Pending verification ({pending.length})</h3>
      <table>
        <thead><tr><th>Ref</th><th>Provider</th><th>Amount ¢</th><th>Actions</th></tr></thead>
        <tbody>{pending.map((p) => (
          <tr key={p.id}>
            <td>{p.provider_ref}</td><td>{p.provider}</td><td>{p.amount_cents}</td>
            <td><button onClick={() => confirm(p.id)}>Confirm paid</button>{' '}<button onClick={() => reject(p.id)}>Reject</button></td>
          </tr>))}</tbody>
      </table>
      <h3 style={{ marginTop: 24 }}>All orders (click row for timeline)</h3>
      <table>
        <thead><tr><th>Order</th><th>Status</th><th>Total ¢</th><th>Technician</th></tr></thead>
        <tbody>{orders.map((o) => (
          <tr key={o.id} onClick={() => setSelected(o)} style={{ cursor: 'pointer', opacity: selected?.id === o.id ? 1 : 0.85 }}>
            <td>{String(o.id).slice(0, 8)}</td><td>{o.status}</td><td>{o.total_cents}</td><td>{o.technician ? String(o.technician).slice(0, 8) : '—'}</td>
          </tr>))}</tbody>
      </table>
      {selected && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>Detail — {String(selected.id).slice(0, 8)}</h3>
          <p>Status: {selected.status} • Total: {selected.total_cents} {selected.currency}</p>
          <p style={{ fontSize: 13 }}>Timeline:</p>
          {(selected.timeline || []).map((s: any, i: number) => <p key={i} style={{ fontSize: 13 }}>• {s.status} — {s.note}</p>)}
          {selected.completion_report && Object.keys(selected.completion_report).length > 0 && (
            <p style={{ fontSize: 13 }}>Report: {JSON.stringify(selected.completion_report)}</p>
          )}
        </div>
      )}
    </div>
  );
}
