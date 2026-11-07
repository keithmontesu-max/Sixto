'use client';
import { useEffect, useState } from 'react';
import { api, type Overview } from '@/lib/api';

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? Math.max(4, (value / max) * 100) : 4;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
        <span>{label}</span><span>{value}</span>
      </div>
      <div style={{ height: 10, background: '#1f2937', borderRadius: 6, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: 'var(--accent)' }} />
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const [range, setRange] = useState('7d');
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setError('');
    api.overview(range)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [range]);

  const maxOrders = Math.max(data?.total_orders || 0, 1);

  return (
    <div>
      <h1>Executive Overview</h1>
      <p style={{ color: 'var(--muted)' }}>Live backend metrics — no demo data.</p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['today', 'yesterday', '7d', '30d', '90d'].map((r) => (
          <button key={r} onClick={() => setRange(r)} style={{ opacity: range === r ? 1 : 0.6 }}>{r}</button>
        ))}
      </div>
      {error && <p style={{ color: '#fca5a5' }}>API error: {error}. Is the backend running?</p>}
      {!data && !error && <p>Loading…</p>}
      {data && (
        <>
          <div className="cards">
            <div className="card"><h3>Total customers</h3><div className="value">{data.total_customers}</div></div>
            <div className="card"><h3>New customers</h3><div className="value">{data.new_customers}</div></div>
            <div className="card"><h3>Registered devices</h3><div className="value">{data.registered_devices}</div></div>
            <div className="card"><h3>Active technicians</h3><div className="value">{data.active_technicians}</div></div>
            <div className="card"><h3>Orders</h3><div className="value">{data.total_orders}</div></div>
            <div className="card"><h3>Completed</h3><div className="value">{data.completed_orders}</div></div>
            <div className="card"><h3>Failed</h3><div className="value">{data.failed_orders}</div></div>
            <div className="card"><h3>Net revenue (¢)</h3><div className="value">{data.net_revenue_cents}</div></div>
            <div className="card"><h3>Active sessions</h3><div className="value">{data.active_sessions}</div></div>
          </div>
          <div className="card" style={{ marginTop: 16 }}>
            <h3>Order mix (last {range})</h3>
            <Bar label="Total" value={data.total_orders} max={maxOrders} />
            <Bar label="Completed" value={data.completed_orders} max={maxOrders} />
            <Bar label="Failed" value={data.failed_orders} max={maxOrders} />
            <Bar label="New customers" value={data.new_customers} max={maxOrders} />
          </div>
        </>
      )}
    </div>
  );
}
