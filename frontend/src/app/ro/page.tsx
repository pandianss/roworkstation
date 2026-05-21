import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard | RO Workstation",
  description: "Dindigul Regional Office employee dashboard. Quick access to regional analytics, campaign management, and operational tools.",
};

import {
  getMISData, getUnits,
  getMe,
  formatCrore,
  type MISRecord,
} from "@/lib/api";

export const dynamic = "force-dynamic";

import NavBar     from "@/components/NavBar";
import MetricCard from "@/components/MetricCard";
import SectionChart from "@/components/SectionChart";
import Link from "next/link";
import styles from "@/styles/components.module.css";

async function getData() {
  const [misRes, unitsRes] = await Promise.allSettled([
    getMISData(),
    getUnits(),
  ]);
  const misData = misRes.status === "fulfilled" ? misRes.value.data : [];
  const units   = unitsRes.status === "fulfilled" ? unitsRes.value.units : [];
  return { misData, units };
}

function computeKPIs(misData: MISRecord[]) {
  if (!misData.length) return null;
  const latestDate = misData.reduce((max, r) => (r.DATE > max ? r.DATE : max), misData[0].DATE);
  const latest = misData.filter((r) => r.DATE === latestDate && r.SOL !== 3933);
  const totalDeposits = latest.reduce((s, r) => s + (r["TOTAL DEPOSITS"] ?? 0), 0);
  const totalAdv      = latest.reduce((s, r) => s + (r.ADV ?? 0), 0);
  const casa          = latest.reduce((s, r) => s + (r.CASA ?? 0), 0);
  const cdRatioAvg    = latest.length
    ? latest.reduce((s, r) => s + (r["CD RATIO"] ?? 0), 0) / latest.length
    : 0;
  return { latestDate, totalDeposits, totalAdv, casa, cdRatio: cdRatioAvg };
}

function computeTrend(misData: MISRecord[]) {
  const byDate: Record<string, { deposits: number; advances: number }> = {};
  misData.filter((r) => r.SOL !== 3933).forEach((r) => {
    const d = r.DATE?.substring(0, 10) ?? "";
    if (!byDate[d]) byDate[d] = { deposits: 0, advances: 0 };
    byDate[d].deposits += r["TOTAL DEPOSITS"] ?? 0;
    byDate[d].advances += r.ADV ?? 0;
  });
  return Object.entries(byDate)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-8)
    .map(([date, v]) => ({
      date: date.substring(5),
      "Total Deposits": v.deposits,
      "Total Advances": v.advances,
    }));
}

const NAV_CARDS = [
  {
    icon: "📊", title: "MIS Analytics",    desc: "Date-wise deposits, advances, CD ratio and performer rankings.",
    href: "/ro/mis",         color: "hsl(217,91%,55%)",
  },
  {
    icon: "🎂", title: "Anniversary Portal", desc: "Branch founding anniversaries and staff birthday/retirement events.",
    href: "/ro/anniversary", color: "hsl(280,70%,65%)",
  },
  {
    icon: "🗄️", title: "Central Archive",  desc: "Search and browse all regional circulars and notices.",
    href: "/ro/archive",     color: "hsl(197,80%,50%)",
  },
  {
    icon: "🚀", title: "Campaigns",        desc: "Active and completed regional business campaigns.",
    href: "/ro/campaigns",   color: "hsl(38,95%,55%)",
  },
  {
    icon: "🏆", title: "Performance",      desc: "Branch-wise ranked performance across key metrics.",
    href: "/ro/performance", color: "hsl(158,76%,46%)",
  },
  {
    icon: "🛡️", title: "Field Guardian",  desc: "Follow-up tracker for field issues and escalations.",
    href: "/ro/guardian",    color: "hsl(0,84%,60%)",
  },
  {
    icon: "🔎", title: "Branch Visits",    desc: "Schedule and records of RO branch inspection visits.",
    href: "/ro/visits",      color: "hsl(197,80%,50%)",
  },
  {
    icon: "🛠️", title: "Wizards",         desc: "Document generation wizards for notes, letters and communications.",
    href: "/ro/wizards",     color: "hsl(257,70%,65%)",
  },
];

export default async function RODashboardPage() {
  const [{ misData, units }, user] = await Promise.all([getData(), getMe()]);
  const kpis  = computeKPIs(misData);
  const trend = computeTrend(misData);
  const activeUnits = units.filter((u) => u.Type !== "REGIONAL OFFICE" && u.Active);

  return (
    <>
      <NavBar activePage="ro" user={user} />

      <main className="container">
        {/* ── HERO ──────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              RO Staff · Live Data
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle}>RO Workstation Dashboard</h1>
            <p className={styles.heroSubtitle}>
              Welcome back, <strong style={{ color: "#fff" }}>{user.name}</strong>.
              Full access to regional analytics, campaigns, and operational tools.
            </p>
            {kpis && (
              <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 10, padding: "0.65rem 1.1rem", backdropFilter: "blur(8px)" }}>
                  <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "rgba(255,255,255,0.55)", letterSpacing: "0.1em", textTransform: "uppercase" }}>As of</div>
                  <div style={{ fontWeight: 700, color: "#fff", fontSize: "0.88rem" }}>{kpis.latestDate}</div>
                </div>
                <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 10, padding: "0.65rem 1.1rem", backdropFilter: "blur(8px)" }}>
                  <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "rgba(255,255,255,0.55)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Network</div>
                  <div style={{ fontWeight: 700, color: "#fff", fontSize: "0.88rem" }}>{activeUnits.length} Active Branches</div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ── KPI STRIP ─────────────────────────────────────── */}
        {kpis && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="section-header">
              <h2>📊 Regional Snapshot</h2>
            </div>
            <div className="grid-4">
              <MetricCard label="Total Deposits"  value={formatCrore(kpis.totalDeposits)} animDelay={0} />
              <MetricCard label="Total Advances"  value={formatCrore(kpis.totalAdv)}      animDelay={60}  accent="green" />
              <MetricCard label="CD Ratio"        value={`${kpis.cdRatio.toFixed(2)}%`}   animDelay={120} accent="amber" />
              <MetricCard label="Low-Cost CASA"   value={formatCrore(kpis.casa)}           animDelay={180} accent="green" />
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── NAVIGATION HUB ────────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-header">
            <h2>🧭 Portal Modules</h2>
          </div>
          <div className="grid-3">
            {NAV_CARDS.map((card) => (
              <Link
                key={card.href}
                href={card.href}
                style={{ textDecoration: "none" }}
              >
                <div
                  className="card animate-fade-up"
                  style={{
                    padding: "1.5rem",
                    cursor: "pointer",
                    borderTop: `3px solid ${card.color}`,
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.65rem",
                  }}
                >
                  <div style={{ fontSize: "2rem", lineHeight: 1 }}>{card.icon}</div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text)" }}>
                    {card.title}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--color-text-muted)", lineHeight: 1.5 }}>
                    {card.desc}
                  </div>
                  <div style={{ fontSize: "0.75rem", fontWeight: 600, color: card.color, marginTop: "auto" }}>
                    Open →
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <div className="divider" />

        {/* ── TREND CHART ───────────────────────────────────── */}
        {trend.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>📈 Business Trajectory</h2>
            </div>
            <div className="card" style={{ padding: "1.5rem" }}>
              <SectionChart
                data={trend}
                xKey="date"
                yKeys={["Total Deposits", "Total Advances"]}
                title="Regional Business Growth"
                kind="area"
                height={280}
              />
            </div>
          </section>
        )}

        {/* ── FOOTER ───────────────────────────────────────── */}
        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ fontWeight: 700, color: "var(--color-text)" }}>RO Workstation</div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>
              Dindigul Regional Office · Powered by FastAPI + Next.js
            </div>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>
            Data refreshes every 60 seconds
          </div>
        </footer>
      </main>
    </>
  );
}
