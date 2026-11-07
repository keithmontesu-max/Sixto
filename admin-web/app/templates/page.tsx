'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function TemplatesPage() {
  const [apiKey, setApiKey] = useState('');
  const [templates, setTemplates] = useState<any>({});
  const [text, setText] = useState('');

  useEffect(() => {
    if (!apiKey) return;
    fetch(`${API}/templates`, { headers: { Authorization: `Bearer ${apiKey}` } })
      .then((r) => r.json())
      .then((d) => { setTemplates(d.templates); setText(JSON.stringify(d.templates, null, 2)); })
      .catch(() => {});
  }, [apiKey]);

  async function save() {
    try {
      const parsed = JSON.parse(text);
      const r = await fetch(`${API}/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({ templates: parsed }),
      });
      alert(r.ok ? 'Saved' : await r.text());
    } catch { alert('Invalid JSON'); }
  }

  return (
    <div>
      <h1>Notification Templates</h1>
      <p style={{ color: 'var(--muted)' }}>Placeholders: {'{order_id}'} {'{amount}'} {'{code}'}. Placeholders render server-side.</p>
      <input placeholder="Admin token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 16 }} />
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={20} style={{ width: '100%' }} />
      <button onClick={save} style={{ marginTop: 8 }}>Save templates</button>
    </div>
  );
}
