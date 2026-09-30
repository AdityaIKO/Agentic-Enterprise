import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Kraka Ops Copilot", description: "Software agents that run the paperwork side of a charcoal trading and production business." };

const nav: [string, [string, string][]][] = [
  ["Overview", [["/", "Today"], ["/audit", "Audit log"]]],
  ["Sell", [["/inquiries", "Inquiries (RFQ agent)"], ["/orders", "Orders"], ["/marketing", "Marketing agent"]]],
  ["Supply", [["/producers", "Producers"], ["/production", "Own production"]]],
  ["Money", [["/finance", "Finance agent"]]],
  ["Setup", [["/settings", "Settings"]]],
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="side">
            <h1>Kraka Ops Copilot</h1>
            <small>Charcoal trading and production</small>
            {nav.map(([g, links]) => (
              <div key={g}>
                <div className="grp">{g}</div>
                {links.map(([h, t]) => <Link key={h} href={h}>{t}</Link>)}
              </div>
            ))}
          </nav>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
