'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function AssistantPage() {
  const [apiKey, setApiKey] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  async function ask() {
    const r = await fetch(`${API}/assistant/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) },
      body: JSON.stringify({ question, manufacturer, model }),
    });
    const data = await r.json();
    setAnswer(data.answer || JSON.stringify(data));
  }

  return (
    <div>
      <h1>Assistant (controlled)</h1>
      <p style={{ color: 'var(--muted)' }}>Explains approved records only. Never invents methods, never authorizes ops.</p>
      <input placeholder="Access token" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
      <input placeholder="Manufacturer (e.g. Xiaomi)" value={manufacturer} onChange={(e) => setManufacturer(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
      <input placeholder="Model (e.g. Mi 10)" value={model} onChange={(e) => setModel(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
      <input placeholder="Question" value={question} onChange={(e) => setQuestion(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
      <button onClick={ask}>Ask</button>
      {answer && <p style={{ marginTop: 16 }}>{answer}</p>}
    </div>
  );
}
