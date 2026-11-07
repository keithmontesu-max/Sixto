'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Termux() {
  const [token, setToken] = useState(() => (typeof window !== 'undefined' ? sessionStorage.getItem('tech_token') || '' : ''));
  const [model, setModel] = useState('');
  const [result, setResult] = useState<any>(null);

  async function check() {
    if (!model.trim()) return;
    const [mfr, mod] = model.split('/').map((s) => s.trim());
    const r = await fetch(`${API}/compatibility/lookup?manufacturer=${encodeURIComponent(mfr)}&model=${encodeURIComponent(mod)}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setResult(await r.json());
  }

  return (
    <div>
      <h1>Termux Auto-Root (No PC — Rooted Phone)</h1>
      <p style={{ color: '#94a3b8' }}>Runs on the phone you own (already unlocked+rooted). First unlock still needs PC fastboot. After that, updates are on-device.</p>
      <div className="card">
        <h3>1. Termux setup (once)</h3>
        <pre style={{ fontSize: 12 }}>{`pkg install -y root-repo
pkg install -y git
git clone <your sixto repo>
cd sixto/backend/scripts
su -c "sh auto_root_termux.sh --boot ~/Downloads/boot.img --magisk ~/Downloads/Magisk-v27.apk"`}</pre>
      </div>
      <div className="card">
        <h3>2. Check before you patch</h3>
        <input placeholder="Manufacturer / Model — e.g. Xiaomi / Redmi Note 12" value={model} onChange={(e) => setModel(e.target.value)} style={{ width: '100%' }} />
        <button onClick={check} style={{ marginTop: 8 }}>Check rootability</button>
        {result && (
          <div style={{ marginTop: 8 }}>
            <p>Root: {result.root?.classification} (eligible: {String(result.root?.eligible)})</p>
            <p>Bootloader: {result.bootloader?.classification} (eligible: {String(result.bootloader?.eligible)})</p>
            {result.root?.reason && <p>{result.root.reason}</p>}
          </div>
        )}
      </div>
      <div className="card">
        <h3>3. Patch (you tap, we verify)</h3>
        <p style={{ fontSize: 13 }}>Magisk → Install → Patch a file → stock <code>boot.img</code> → copy <code>magisk_patched.img</code> to <code>~/patched/magisk.img</code> → Magisk → Direct install → reboot → verify 4-check in SIXTO app.</p>
        <p style={{ fontSize: 12 }}>Wrong-build boot = bootloop. Match build fingerprint exactly. Back up first.</p>
      </div>
    </div>
  );
}
