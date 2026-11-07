import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SIXTO ROOT X — Admin Command Center',
  description: 'Commercial operations, compatibility, finance, and security control',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div className="brand">SIXTO ROOT X</div>
            <div className="brand-sub">Admin Command Center</div>
            <nav>
              <a href="/">Executive Overview</a>
              <a href="/customers">Customers</a>
              <a href="/technicians">Technicians</a>
              <a href="/compatibility">Compatibility</a>
              <a href="/root-methods">Root Methods</a>
              <a href="/services">Services & Pricing</a>
              <a href="/orders">Orders & Payments</a>
              <a href="/updates">Update Center</a>
              <a href="/bugs">Bug Management</a>
              <a href="/finance">Finance</a>
              <a href="/config">Business Config</a>
              <a href="/templates">Notification Templates</a>
              <a href="/assistant">Assistant</a>
              <a href="/tech-portal">Technician Portal</a>
              <a href="/audit">Audit & Security</a>
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
