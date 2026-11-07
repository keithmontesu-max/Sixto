'use client';
import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [msg, setMsg] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg('Signing in via API…');
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, totp_code: totp }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      // Token exchange/session cookie is handled by your auth strategy in production.
      // Here we store nothing sensitive — redirect to dashboard.
      setMsg(`Signed in as ${email}. Redirecting…`);
      window.location.href = '/';
    } catch (e: any) {
      setMsg(`Login failed: ${e.message}`);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: '40px auto' }}>
      <h1>Admin Login</h1>
      <p style={{ color: 'var(--muted)' }}>OWNER / SUPER_ADMIN / ADMIN only. MFA required when enabled.</p>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <input placeholder="MFA code (if enabled)" value={totp} onChange={(e) => setTotp(e.target.value)} />
        <button type="submit">Sign in</button>
      </form>
      {msg && <p style={{ marginTop: 12 }}>{msg}</p>}
    </div>
  );
}
