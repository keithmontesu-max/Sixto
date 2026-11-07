'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function TechLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [msg, setMsg] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, totp_code: totp }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      // Must be OWNER — verify role before showing engine UI.
      const me = await fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${data.access_token}` } });
      const meJson = await me.json();
      if (meJson.role !== 'OWNER') {
        setMsg('403 — TECHTOOL requires OWNER role. Customer/admin accounts cannot enter.');
        return;
      }
      sessionStorage.setItem('tech_token', data.access_token);
      window.location.href = '/dashboard';
    } catch (e: any) {
      setMsg(`Failed: ${e.message}`);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: '40px auto', fontFamily: 'system-ui' }}>
      <h1>SIXTO TECHTOOL</h1>
      <p style={{ color: '#94a3b8' }}>Owner-only engine. Not the customer app. MFA required.</p>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <input placeholder="Owner email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <input placeholder="MFA code" value={totp} onChange={(e) => setTotp(e.target.value)} required />
        <button type="submit">Enter TECHTOOL</button>
      </form>
      {msg && <p>{msg}</p>}
    </div>
  );
}
