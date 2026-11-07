'use client';
import { useState } from 'react';

const LOCAL = 'http://127.0.0.1:8001';
const ROOT_STEPS = [
  { id: 'detect', label: 'Detect my phone' },
  { id: 'patch_verify', label: 'Verify patched image' },
  { id: 'install', label: 'Direct install (tap in Magisk)' },
  { id: 'verify', label: 'Verify root (4-check)' },
];
const OTG_STEPS = [
  { id: 'otg_devices', label: 'OTG 1 — adb devices' },
  { id: 'otg_reboot', label: 'OTG 2 — reboot bootloader' },
  { id: 'otg_getvar', label: 'OTG 3 — getvar unlocked?' },
  { id: 'otg_unlock', label: 'OTG 4 — flashing unlock' },
  { id: 'otg_verify', label: 'OTG 5 — verify unlocked=yes' },
];

const FULL_AUTO = [
  ...OTG_STEPS,
  { id: 'detect', label: 'Then verify headset' },
];

export default function Console() {
  const [log, setLog] = useState<string[]>([]);
  const [status, setStatus] = useState<any>(null);
  const [busy, setBusy] = useState('');
  const [connected, setConnected] = useState(false);

  function push(msg: string) {
    setLog((l) => [...l.slice(-100), msg]);
  }

  async function run(id: string) {
    setBusy(id);
    try {
      const r = await fetch(`${LOCAL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      });
      const data = await r.json();
      push(`✔ ${id}: ${JSON.stringify(data).slice(0, 300)}`);
      if (id === 'detect' && data.result) setStatus(data.result);
    } catch {
      push(`✖ ${id}: unreachable — start Termux Console first`);
    } finally {
      setBusy('');
    }
  }

  async function fullAuto() {
    push('▶ FULL AUTO starting (sequential, stop-on-error)…');
    for (const s of FULL_AUTO) {
      await run(s.id);
    }
    push('▶ FULL AUTO done. Customer taps Vol+ at OTG 4; patch/install need Magisk tap.');
  }

  async function check() {
    try {
      const r = await fetch(`${LOCAL}/status`);
      setStatus(await r.json());
      setConnected(true);
      push('Connected to on-device runner.');
    } catch {
      push('No runner at 127.0.0.1:8001 — run termux_console.py in Termux (guide below).');
    }
  }

  return (
    <div>
      <h1>Installed Console (on this phone) ⭐ OTG-Only</h1>
      <p style={{ color: '#94a3b8' }}>Runs on the <strong>same rooted phone</strong> (localhost). No PC. Customer phone has no Termux — only taps Allow + Vol+.</p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={check}>Connect</button>
        <button onClick={fullAuto} disabled={busy !== ''} style={{ background: '#6ee7b7', color: '#04120b', fontWeight: 800 }}>▶ FULL AUTO (one tap)</button>
      </div>
      {connected && <p style={{ color: '#6ee7b7', fontSize: 13 }}>● On-device runner live</p>}
      {status && <pre style={{ fontSize: 12 }}>{JSON.stringify(status, null, 2)}</pre>}
      <div className="card">
        <h3>OTG Unlock (customer locked phone → your rooted host)</h3>
        {OTG_STEPS.map((s) => (
          <div key={s.id} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
            <button onClick={() => run(s.id)} disabled={busy === s.id}>{s.label}</button>
          </div>
        ))}
        <p style={{ fontSize: 12 }}>At OTG 4: customer taps <strong>Volume UP</strong> on THEIR phone. Wipe occurs. FRP prompt = stop.</p>
      </div>
      <div className="card">
        <h3>Root (after unlock — on customer phone via Magisk)</h3>
        {ROOT_STEPS.map((s) => (
          <div key={s.id} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
            <button onClick={() => run(s.id)} disabled={busy === s.id}>{s.label}</button>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Console log</h3>
        <pre style={{ fontSize: 12, maxHeight: 240, overflow: 'auto' }}>{log.join('\n')}</pre>
      </div>
      <div className="card">
        <h3>Start the runner (Termux, once)</h3>
        <pre style={{ fontSize: 12 }}>{`su
pkg install -y python
python ~/sixto/backend/scripts/termux_console.py --port 8001`}</pre>
        <p style={{ fontSize: 12 }}>Keep Termux running, open this page in the same phone's browser. Reboot kills the server — restart runner, then Verify.</p>
      </div>
    </div>
  );
}
