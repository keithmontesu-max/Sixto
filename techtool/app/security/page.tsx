'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Security() {
  const [token, setToken] = useState('');
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    const t = sessionStorage.getItem('tech_token') || '';
    setToken(t);
    if (!t) return;
    fetch(`${API}/tech/incidents?limit=100`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json()).then(setRows).catch(() => {});
  }, []);

  if (!token) return <p>Not signed in.</p>;
  return (
    <div>
      <h1>Security / Incidents</h1>
      <p style={{ color: '#94a3b8' }}>Failed auth, lockouts, engine actions. Full audit at /admin/audit.</p>
      <table>
        <thead><tr><th>At</th><th>Action</th><th>Target</th></tr></thead>
        <tbody>{rows.map((r) => <tr key={r.id}><td>{String(r.at).slice(0, 19)}</td><td>{r.action}</td><td>{String(r.target).slice(0, 16)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
