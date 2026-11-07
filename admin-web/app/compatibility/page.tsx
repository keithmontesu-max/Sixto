'use client';
import { useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface CompatRow {
  id: string;
  manufacturer: string;
  model: string;
  root_classification: string;
  root_eligible: boolean;
  is_approved: boolean;
  is_excluded: boolean;
}

export default function CompatibilityPage() {
  const [rows, setRows] = useState<CompatRow[]>([]);
  const [form, setForm] = useState({
    manufacturer: '', model: '', model_id: '', hardware_variant: '', firmware_line: '',
    root_classification: 'UNKNOWN', bootloader_classification: 'UNKNOWN',
    root_eligible: false, unlock_eligible: false, supported_method: '',
    is_approved: false, is_excluded: false, exclusion_reason: '', last_tested_date: '',
  });
  const [msg, setMsg] = useState('');
  const [apiKey, setApiKey] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/compatibility/admin/list`, {
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
      if (!res.ok) throw new Error(await res.text());
      setRows(await res.json());
    } catch (e: any) {
      setMsg(`Load failed: ${e.message}`);
    }
  }, [apiKey]);

  useEffect(() => { load(); }, [load]);

  async function upsert(e: React.FormEvent) {
    e.preventDefault();
    setMsg('Saving…');
    try {
      const res = await fetch(`${API}/compatibility/admin/upsert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
        body: JSON.stringify({ ...form, prerequisites: [], known_limitations: [], release_version: '1.0.0' }),
      });
      if (!res.ok) throw new Error(await res.text());
      setMsg('Saved. Only approved records enable customer operations.');
      load();
    } catch (e: any) {
      setMsg(`Save failed: ${e.message}`);
    }
  }

  return (
    <div>
      <h1>Compatibility Management</h1>
      <p style={{ color: 'var(--muted)' }}>
        Exact model + firmware only. Root and bootloader are separate. Vivo is EXCLUDED from Auto Root catalog (business policy).
      </p>
      <p style={{ color: 'var(--muted)', fontSize: 13 }}>
        Admin token (OWNER/SUPER_ADMIN/ADMIN): paste your access_token to call admin APIs.
      </p>
      <input placeholder="Access token" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
        style={{ width: '100%', marginBottom: 16 }} />
      <form onSubmit={upsert} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 24 }}>
        <input placeholder="Manufacturer" value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} required />
        <input placeholder="Model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} required />
        <input placeholder="Model ID" value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })} />
        <input placeholder="Hardware variant" value={form.hardware_variant} onChange={(e) => setForm({ ...form, hardware_variant: e.target.value })} />
        <input placeholder="Firmware line" value={form.firmware_line} onChange={(e) => setForm({ ...form, firmware_line: e.target.value })} />
        <select value={form.root_classification} onChange={(e) => setForm({ ...form, root_classification: e.target.value })}>
          {['ROOTABLE', 'NOT_ROOTABLE', 'BOOTLOADER_UNLOCKABLE', 'BOOTLOADER_LOCKED', 'AUTHORIZATION_REQUIRED', 'PARTIALLY_SUPPORTED', 'UNKNOWN', 'EXCLUDED'].map((v) => <option key={v}>{v}</option>)}
        </select>
        <select value={form.bootloader_classification} onChange={(e) => setForm({ ...form, bootloader_classification: e.target.value })}>
          {['ROOTABLE', 'NOT_ROOTABLE', 'BOOTLOADER_UNLOCKABLE', 'BOOTLOADER_LOCKED', 'AUTHORIZATION_REQUIRED', 'PARTIALLY_SUPPORTED', 'UNKNOWN', 'EXCLUDED'].map((v) => <option key={v}>{v}</option>)}
        </select>
        <select value={form.supported_method} onChange={(e) => setForm({ ...form, supported_method: e.target.value })}>
          <option value="">No method</option>
          <option>Magisk</option>
          <option>KernelSU</option>
          <option>APatch</option>
        </select>
        <label><input type="checkbox" checked={form.root_eligible} onChange={(e) => setForm({ ...form, root_eligible: e.target.checked })} /> Root eligible</label>
        <label><input type="checkbox" checked={form.unlock_eligible} onChange={(e) => setForm({ ...form, unlock_eligible: e.target.checked })} /> Unlock eligible</label>
        <label><input type="checkbox" checked={form.is_approved} onChange={(e) => setForm({ ...form, is_approved: e.target.checked })} /> Approved</label>
        <label><input type="checkbox" checked={form.is_excluded} onChange={(e) => setForm({ ...form, is_excluded: e.target.checked })} /> Excluded</label>
        <input placeholder="Exclusion reason" value={form.exclusion_reason} onChange={(e) => setForm({ ...form, exclusion_reason: e.target.value })} />
        <input placeholder="Last tested (YYYY-MM-DD)" value={form.last_tested_date} onChange={(e) => setForm({ ...form, last_tested_date: e.target.value })} />
        <button type="submit">Save record</button>
      </form>
      {msg && <p>{msg}</p>}
      <table>
        <thead><tr><th>Manufacturer</th><th>Model</th><th>Root class</th><th>Root eligible</th><th>Approved</th><th>Excluded</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.manufacturer}</td><td>{r.model}</td><td>{r.root_classification}</td>
              <td>{r.root_eligible ? 'yes' : 'no'}</td><td>{r.is_approved ? 'yes' : 'no'}</td><td>{r.is_excluded ? 'yes' : 'no'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
