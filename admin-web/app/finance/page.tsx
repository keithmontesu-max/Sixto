'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function FinancePage() {
  const [apiKey, setApiKey] = useState('');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!apiKey) return;
    fetch(`${API}/admin/finance`, { headers: { Authorization: `Bearer ${apiKey}` } })
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, [apiKey]);

  return (
    <div>
      <h1>Finance</h1>
      <p style={{ color: 'var(--muted)' }}>Verified transactions only (not orders created).</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      {apiKey && (
        <button onClick={() => {
          window.open(`${API}/admin/finance/export`, '_blank');
        }} style={{ marginBottom: 16 }}>Download CSV (verified payments)</button>
      )}
      {data && (
        <div className="cards">
          <div className="card"><h3>Gross (¢)</h3><div className="value">{data.gross_cents}</div></div>
          <div className="card"><h3>Refunds (¢)</h3><div className="value">{data.refunds_cents}</div></div>
          <div className="card"><h3>Net (¢)</h3><div className="value">{data.net_cents}</div></div>
          <div className="card"><h3>Pending (¢)</h3><div className="value">{data.pending_cents}</div></div>
          <div className="card"><h3>Orders</h3><div className="value">{data.orders}</div></div>
          <div className="card"><h3>Avg order (¢)</h3><div className="value">{Math.round(data.avg_order_value_cents)}</div></div>
        </div>
      )}
    </div>
  );
}
