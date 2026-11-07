'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Analyze() {
  const [token, setToken] = useState(() => (typeof window !== 'undefined' ? sessionStorage.getItem('tech_token') || '' : ''));
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await fetch(`${API}/tech/analyze-photo`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h1>Photo Check (Owner Only)</h1>
      <p style={{ color: '#94a3b8' }}>Upload a <strong>screenshot</strong> of Settings → About phone. Physical phone photos rarely read kernel. OCR extracts, you verify.</p>
      <input type="file" accept="image/*" onChange={upload} />
      {error && <p style={{ color: '#fca5a5' }}>{error}</p>}
      {result && (
        <div className="card">
          <h3>Extracted</h3>
          <pre>{JSON.stringify(result.signals, null, 2)}</pre>
          <p style={{ fontSize: 13 }}>{result.ocr_note} • Hash {result.image_hash}</p>
          {result.compatibility && (
            <div>
              <h3>Root? {result.compatibility.root.classification} (eligible: {result.compatibility.root.eligible ? 'yes' : 'no'})</h3>
              <h3>Bootloader? {result.compatibility.bootloader.classification} (eligible: {result.compatibility.bootloader.eligible ? 'yes' : 'no'})</h3>
              {result.compatibility.supported_method && <p>Method: {result.compatibility.supported_method}</p>}
            </div>
          )}
          <p style={{ fontSize: 13 }}>{result.instruction}</p>
        </div>
      )}
    </div>
  );
}
