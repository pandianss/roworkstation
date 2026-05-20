import { notFound } from "next/navigation";
import {
  getMISData, getUnits, getDepartments,
  getCirculars, getCampaigns,
  formatCrore,
  type MISRecord,
} from "@/lib/api";

import NavBar           from "@/components/NavBar";
import MetricCard       from "@/components/MetricCard";
import SectionChart     from "@/components/SectionChart";
import AnnouncementCard from "@/components/AnnouncementCard";
import CoordinationForm from "@/components/CoordinationForm";
import styles from "@/styles/components.module.css";

interface Props {
  params: Promise<{ sol: string }>;
}

async function getData(sol: string) {
  const [misRes, unitsRes, deptsRes, circularsRes, campaignsRes] =
    await Promise.allSettled([
      getMISData(),
      getUnits(),
      getDepartments(),
      getCirculars(),
      getCampaigns(),
    ]);

  const misData   = misRes.status    === "fulfilled" ? misRes.value.data           : [];
  const units     = unitsRes.status  === "fulfilled" ? unitsRes.value.units        : [];
  const depts     = deptsRes.status  === "fulfilled" ? deptsRes.value.departments  : [];
  const circulars = circularsRes.status  === "fulfilled" ? circularsRes.value.circulars  : [];
  const campaigns = campaignsRes.status  === "fulfilled" ? campaignsRes.value.campaigns  : [];

  const solNum = parseInt(sol, 10);
  const unit = units.find((u) => u.Code === sol || parseInt(u.Code, 10) === solNum);
  const branchData = misData.filter((r) => r.SOL === solNum);

  return { branchData, unit, depts, circulars, campaigns, solNum };
}

function getLatestKPIs(branchData: MISRecord[]) {
  if (!branchData.length) return null;
  const latestDate = branchData.reduce((max, r) => (r.DATE > max ? r.DATE : max), branchData[0].DATE);
  const latest = branchData.filter((r) => r.DATE === latestDate);
  const row = latest[0];
  const totalDep = row?.["TOTAL DEPOSITS"] ?? 0;
  return {
    latestDate,
    totalDeposits: totalDep,
    totalAdv:      row?.ADV ?? 0,
    casa:          row?.CASA ?? 0,
    cdRatio:       row?.["CD RATIO"] ?? 0,
    npa:           row?.["NPA %"] ?? 0,
    casaPct:       totalDep > 0 ? ((row?.CASA ?? 0) / totalDep) * 100 : 0,
  };
}

function computeBranchTrend(branchData: MISRecord[]) {
  return branchData
    .sort((a, b) => a.DATE.localeCompare(b.DATE))
    .slice(-8)
    .map((r) => ({
      date: r.DATE.substring(5),
      "Total Deposits": r["TOTAL DEPOSITS"] ?? 0,
      "Total Advances": r.ADV ?? 0,
    }));
}

export default async function BranchPortalPage({ params }: Props) {
  const { sol } = await params;
  const { branchData, unit, depts, circulars, campaigns, solNum } = await getData(sol);

  if (!unit && branchData.length === 0) notFound();

  const branchName = unit?.Name ?? `Branch SOL ${sol}`;
  const kpis = getLatestKPIs(branchData);
  const trend = computeBranchTrend(branchData);

  const activeCampaigns   = campaigns.filter((c) => c.status === "Active");
  const completedCampaigns = campaigns.filter((c) => c.status === "Completed");

  return (
    <>
      <NavBar activePage="branch" sol={sol} />

      <main className="container">
        {/* ── BRANCH HERO ──────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero} style={{ background: "linear-gradient(135deg, hsl(158,76%,20%) 0%, hsl(158,60%,35%) 100%)", marginBottom: "2rem" }}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              SOL {solNum}
            </div>
            <div className={styles.heroEyebrow}>Branch Portal</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)" }}>{branchName}</h1>
            {kpis && (
              <p className={styles.heroSubtitle} style={{ marginTop: "0.75rem" }}>
                Data as of <strong style={{ color: "#fff" }}>{kpis.latestDate}</strong>
              </p>
            )}
          </div>
        </section>

        {/* ── BRANCH KPIs ──────────────────────────────────────── */}
        {kpis ? (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="section-header">
              <h2>📊 Branch Performance</h2>
            </div>
            <div className="grid-4">
              <MetricCard label="Total Deposits"  value={formatCrore(kpis.totalDeposits)} animDelay={0} />
              <MetricCard label="Total Advances"  value={formatCrore(kpis.totalAdv)}      animDelay={60}  accent="green" />
              <MetricCard label="CASA Ratio"      value={`${kpis.casaPct.toFixed(2)}%`}   animDelay={120} accent="amber" />
              <MetricCard label="NPA %"           value={`${kpis.npa}%`}                  animDelay={180} accent="amber" />
            </div>
          </section>
        ) : (
          <div className={styles.emptyState} style={{ marginTop: "2rem" }}>
            <div className={styles.emptyIcon}>📭</div>
            <span>No MIS data found for SOL {solNum}</span>
          </div>
        )}

        <div className="divider" />

        {/* ── BUSINESS TREND ────────────────────────────────────── */}
        {trend.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>📈 Branch Business Trend</h2>
            </div>
            <div className="card" style={{ padding: "1.5rem" }}>
              <SectionChart
                data={trend}
                xKey="date"
                yKeys={["Total Deposits", "Total Advances"]}
                title={`${branchName} — Deposits & Advances`}
                kind="area"
                height={280}
              />
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── CAMPAIGNS ─────────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🚀 Ongoing Campaigns</h2>
          </div>
          {activeCampaigns.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📣</div>
              <span>No active campaigns at the moment</span>
            </div>
          ) : (
            <div className="grid-2">
              {activeCampaigns.map((c, i) => (
                <div key={i} className={`card ${styles.campaignCard} animate-fade-up`} style={{ animationDelay: `${i * 60}ms` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                    <div className={styles.campaignName}>{c.name}</div>
                    <span className="badge badge--green">Active</span>
                  </div>
                  <div className={styles.campaignDates}>
                    {c.start_date} → {c.end_date}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--color-text-muted)", marginBottom: "0.75rem" }}>
                    <strong>Focus:</strong> {c.target_metric} &nbsp;·&nbsp;
                    <strong>Target:</strong> ₹{c.target_value} Cr
                  </div>
                  <div className={styles.progressTrack}>
                    <div className={styles.progressFill} style={{ width: "65%" }} />
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)", marginTop: "4px" }}>Campaign in progress</div>
                </div>
              ))}
            </div>
          )}

          {completedCampaigns.length > 0 && (
            <div style={{ marginTop: "1.5rem" }}>
              <h4 style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", marginBottom: "0.75rem" }}>
                ✅ Recently Completed
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {completedCampaigns.slice(0, 3).map((c, i) => (
                  <div key={i} style={{ fontSize: "0.85rem", color: "var(--color-text-faint)", padding: "0.5rem 0.75rem", background: "var(--color-surface-2)", borderRadius: "var(--radius-sm)" }}>
                    ✅ {c.name} · Target: ₹{c.target_value} Cr · Ended {c.end_date}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        <div className="divider" />

        {/* ── CIRCULARS ─────────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>📢 Regional Circulars</h2>
          </div>
          {circulars.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📭</div>
              <span>No circulars published</span>
            </div>
          ) : (
            <div className="grid-3">
              {circulars.slice(0, 6).map((c, i) => (
                <AnnouncementCard key={c.id} circular={c} animDelay={i * 60} />
              ))}
            </div>
          )}
        </section>

        <div className="divider" />

        {/* ── RO COORDINATION ───────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>💬 Regional Office Coordination</h2>
          </div>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
            Send requests or inquiries directly to Regional Office departments.
          </p>
          <div style={{ maxWidth: "640px" }}>
            <div className="card" style={{ padding: "1.75rem" }}>
              <CoordinationForm sol={sol} departments={depts} />
            </div>
          </div>
        </section>

        {/* ── FOOTER ───────────────────────────────────────────── */}
        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ fontWeight: 700, color: "var(--color-text)" }}>{branchName}</div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>SOL {solNum} · Powered by FastAPI + Next.js</div>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>Data refreshes every 60 seconds</div>
        </footer>
      </main>
    </>
  );
}
