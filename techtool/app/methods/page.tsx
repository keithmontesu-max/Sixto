'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Methods() {
  const [token, setToken] = useState('');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const t = sessionStorage.getItem('tech_token') || '';
    setToken(t);
    if (!t) return;
    fetch(`${API}/root-methods`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json()).then(setData).catch(() => {});
  }, []);

  if (!token) return <p>Not signed in.</p>;
  return (
    <div>
      <h1>Root Methods — Owner Control</h1>
      {(data?.methods || []).map((m: any) => (
        <div key={m.method} className="card">
          <h3>{m.method} ({m.count} records)</h3>
          <ul style={{ fontSize: 13 }}>
            {m.records.slice(0, 6).map((r: any) => <li key={r.id}>{r.manufacturer} {r.model}</li>)}
          </ul>
        </div>
      ))}
    </div>
  );
}
