'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Flash() {
  const [token, setToken] = useState('');
  const [img, setImg] = useState('~/Downloads/magisk.img');
  const [vbmeta, setVbmeta] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => { setToken(sessionStorage.getItem('tech_token') || ''); }, []);

  async function gen() {
    const r = await fetch(`${API}/flash/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ patched_image: img, do_vbmeta: vbmeta }),
    });
    setPlan(await r.json());
  }

  return (
    <div>
      <h1>Auto-Flash Console (Owner Only)</h1>
      <p style={{ color: '#94a3b8' }}>Supervised Magisk flash. Backend plans; execution runs on your PC via <code>scripts/auto_flash.py</code>. Never blind-flash.</p>
      <input value={img} onChange={(e) => setImg(e.target.value)} placeholder="Patched image path on PC" style={{ width: '100%', marginBottom: 8 }} />
      <label style={{ display: 'block', marginBottom: 8 }}><input type="checkbox" checked={vbmeta} onChange={(e) => setVbmeta(e.target.checked)} /> Also flash vbmeta (only if record requires)</label>
      <button onClick={gen}>Generate plan</button>
      {plan && (
        <div className="card">
          <h3>Flash {plan.flash_id} — {plan.ok ? 'ready' : 'blocked'}</h3>
          {plan.ok && <p>SHA256: {plan.image_sha256}</p>}
          {plan.reason && <p style={{ color: '#fca5a5' }}>{plan.reason}</p>}
          {(plan.steps || []).map((s: any, i: number) => <p key={i} style={{ fontSize: 13 }}>{i + 1}. <code>{s.cmd}</code> (timeout {s.timeout}s)</p>)}
          {(plan.warnings || []).map((w: string, i: number) => <p key={i} style={{ fontSize: 12 }}>⚠ {w}</p>)}
          <p style={{ fontSize: 13 }}>On PC: <code>python backend/scripts/auto_flash.py --img {img}{vbmeta ? ' --vbmeta' : ''}</code></p>
        </div>
      )}
      {msg && <p>{msg}</p>}
    </div>
  );
}
