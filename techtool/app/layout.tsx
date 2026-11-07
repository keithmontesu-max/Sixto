import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'SIXTO TECHTOOL — Owner Engine' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><body>
      <div className="shell">
        <aside className="sidebar">
          <div className="brand">SIXTO TECHTOOL</div>
          <div className="brand-sub">OWNER-ONLY ENGINE</div>
          <nav>
            <a href="/dashboard">Engine Status</a>
            <a href="/analyze">Photo Check</a>
            <a href="/console">Console (On-Phone) ⭐</a>
            <a href="/methods">Root Methods</a>
            <a href="/security">Security / Incidents</a>
          </nav>
          <p style={{ color: '#94a3b8', fontSize: 12 }}>OTG-only: your rooted phone unlocks/roots customer phones via USB. No PC needed. Customer APK cannot call /tech/* (server 403).</p>
        </aside>
        <main className="main">{children}</main>
      </div>
    </body></html>
  );
}
