import {
  getMISData, getUnits, getDepartments,
  getCirculars, getAchievements,
  formatCrore, formatIndian,
  type MISRecord, type Unit,
} from "@/lib/api";

import NavBar          from "@/components/NavBar";
import MetricCard      from "@/components/MetricCard";
import SectionChart    from "@/components/SectionChart";
import BranchDirectory from "@/components/BranchDirectory";
import DemographicsPanel from "@/components/DemographicsPanel";
import AnnouncementCard from "@/components/AnnouncementCard";
import AchievementCard  from "@/components/AchievementCard";

import styles from "@/styles/components.module.css";

// ── Page-level data fetch (ISR, revalidates every 60s) ──────────────────────
async function getData() {
  const [misRes, unitsRes, deptsRes, circularsRes, achievementsRes] =
    await Promise.allSettled([
      getMISData(),
      getUnits(),
      getDepartments(),
      getCirculars(),
      getAchievements(),
    ]);

  const misData    = misRes.status    === "fulfilled" ? misRes.value.data            : [];
  const units      = unitsRes.status  === "fulfilled" ? unitsRes.value.units         : [];
  const depts      = deptsRes.status  === "fulfilled" ? deptsRes.value.departments   : [];
  const circulars  = circularsRes.status  === "fulfilled" ? circularsRes.value.circulars  : [];
  const achievements = achievementsRes.status === "fulfilled" ? achievementsRes.value.achievements : [];

  return { misData, units, depts, circulars, achievements };
}

// ── Compute KPIs from latest date ───────────────────────────────────────────
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

  // Advances sectoral mix
  const retail = latest.reduce((s, r) => s + (r["TOTAL RETAIL"] ?? 0), 0);
  const agri   = latest.reduce((s, r) => s + (r["CORE AGRI"] ?? 0), 0);
  const msme   = latest.reduce((s, r) => s + (r.MSME ?? 0), 0);
  const other  = Math.max(0, totalAdv - retail - agri - msme);

  // Deposits mix
  const sb    = latest.reduce((s, r) => s + ((r as Record<string, number>).SB ?? (r as Record<string, number>).sb ?? 0), 0);
  const td    = latest.reduce((s, r) => s + ((r as Record<string, number>).TD ?? (r as Record<string, number>).td ?? 0), 0);
  const casaCalc = casa > 0 ? casa : sb; // use CASA if present, else SB

  return {
    latestDate,
    totalDeposits,
    totalAdv,
    casa: casaCalc,
    cdRatio: cdRatioAvg,
    depPieData: [
      { name: "CASA", value: casaCalc },
      { name: "Term Deposits", value: td > 0 ? td : totalDeposits - casaCalc },
    ],
    advPieData: [
      { name: "Retail", value: retail },
      { name: "Agriculture", value: agri },
      { name: "MSME", value: msme },
      { name: "Others", value: other },
    ],
  };
}

// ── FY Trend (last 6 months of data) ───────────────────────────────────────
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
      date: date.substring(5), // MM-DD
      "Total Deposits": v.deposits,
      "Total Advances": v.advances,
    }));
}

// ── Recovery data ────────────────────────────────────────────────────────────
function computeRecovery(misData: MISRecord[], latestDate: string) {
  const latest = misData.filter((r) => r.DATE === latestDate && r.SOL !== 3933);
  return [
    { quarter: "Q1", value: latest.reduce((s, r) => s + (r["REC Q1"] ?? 0), 0) },
    { quarter: "Q2", value: latest.reduce((s, r) => s + (r["REC Q2"] ?? 0), 0) },
    { quarter: "Q3", value: latest.reduce((s, r) => s + (r["REC Q3"] ?? 0), 0) },
    { quarter: "Q4", value: latest.reduce((s, r) => s + (r["REC Q4"] ?? 0), 0) },
  ];
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default async function GuestPortalPage() {
  const { misData, units, depts, circulars, achievements } = await getData();

  const kpis    = computeKPIs(misData);
  const trend   = computeTrend(misData);
  const recovery = kpis ? computeRecovery(misData, kpis.latestDate) : [];

  const activeDepts = depts.filter((d) => d.Active);
  const activeUnits = units.filter((u) => u.Type !== "REGIONAL OFFICE" && u.Active);

  // RM info — first unit with type REGIONAL OFFICE gives head name
  const roUnit = units.find((u) => u.Type === "REGIONAL OFFICE");
  const rmName = roUnit?.Head ?? "The Regional Manager";

  return (
    <>
      <NavBar activePage="guest" />

      <main className="container">
        {/* ── HERO ─────────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Live Regional Data
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle}>Regional Business Portal</h1>
            <p className={styles.heroSubtitle}>
              Transparency and Excellence in Banking. Overview of regional performance,
              district coverage, and organizational achievements.
            </p>
            {kpis && (
              <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "0.75rem 1.25rem", backdropFilter: "blur(8px)" }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "rgba(255,255,255,0.6)", letterSpacing: "0.1em", textTransform: "uppercase" }}>As of</div>
                  <div style={{ fontWeight: 700, color: "#fff" }}>{kpis.latestDate}</div>
                </div>
                <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "0.75rem 1.25rem", backdropFilter: "blur(8px)" }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "rgba(255,255,255,0.6)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Network</div>
                  <div style={{ fontWeight: 700, color: "#fff" }}>{activeUnits.length} Active Branches</div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ── KPI METRICS ──────────────────────────────────────── */}
        {kpis && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="section-header">
              <h2>📊 Regional Business Snapshot</h2>
            </div>
            <div className="grid-4">
              <MetricCard label="Total Deposits"  value={formatCrore(kpis.totalDeposits)} animDelay={0} />
              <MetricCard label="Total Advances"  value={formatCrore(kpis.totalAdv)}      animDelay={60}  accent="green" />
              <MetricCard label="CD Ratio"        value={`${kpis.cdRatio.toFixed(2)}%`}   animDelay={120} accent="amber" />
              <MetricCard label="Low Cost (CASA)" value={formatCrore(kpis.casa)}           animDelay={180} accent="green" />
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── PORTFOLIO CHARTS ─────────────────────────────────── */}
        {kpis && (
          <section className="section">
            <div className="section-header">
              <h2>🥧 Portfolio Composition</h2>
            </div>
            <div className="grid-2">
              <div className="card" style={{ padding: "1.5rem" }}>
                <SectionChart
                  data={kpis.depPieData}
                  xKey="name"
                  yKeys="value"
                  title="Deposit Mix"
                  kind="pie"
                  height={260}
                />
              </div>
              <div className="card" style={{ padding: "1.5rem" }}>
                <SectionChart
                  data={kpis.advPieData}
                  xKey="name"
                  yKeys="value"
                  title="Advances Sectoral Mix (RAM)"
                  kind="pie"
                  height={260}
                />
              </div>
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── BUSINESS TRAJECTORY ──────────────────────────────── */}
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
                height={300}
              />
            </div>
          </section>
        )}

        {/* ── RECOVERY ─────────────────────────────────────────── */}
        {recovery.length > 0 && (
          <>
            <div className="divider" />
            <section className="section">
              <div className="section-header">
                <h2>💰 Quarterly Recovery</h2>
              </div>
              <div className="card" style={{ padding: "1.5rem" }}>
                <SectionChart
                  data={recovery}
                  xKey="quarter"
                  yKeys="value"
                  title="Recovery Progress (₹ Cr)"
                  kind="bar"
                  height={240}
                />
              </div>
            </section>
          </>
        )}

        <div className="divider" />

        {/* ── DEMOGRAPHICS ─────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🌐 Network Demographics</h2>
          </div>
          <DemographicsPanel units={units} />
        </section>

        <div className="divider" />

        {/* ── ORGANIZATION PANEL ───────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🏛️ Organisation</h2>
          </div>
          <div className="grid-2">
            <div className="card" style={{ padding: "1.5rem" }}>
              <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>Regional Head</div>
              <h3 style={{ fontSize: "1.2rem", color: "var(--color-text)" }}>{rmName}</h3>
              <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>Regional Manager · Dindigul</p>
            </div>
            <div className="card" style={{ padding: "1.5rem" }}>
              <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>Departments</div>
              <h3 style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--color-primary-light)" }}>
                {activeDepts.length}
              </h3>
              <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>Active Specialized Departments</p>
              <div style={{ marginTop: "1rem", display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {activeDepts.slice(0, 8).map((d) => (
                  <span key={d.Code} className="badge badge--blue">{d["Name (En)"]}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <div className="divider" />

        {/* ── BRANCH DIRECTORY ─────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🔍 Regional Branch Directory</h2>
          </div>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
            Instantly find location details, opening dates, and designated unit authorities.
          </p>
          <BranchDirectory units={units} />
        </section>

        <div className="divider" />

        {/* ── ANNOUNCEMENTS ────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>📢 Announcements &amp; Notices</h2>
          </div>
          {circulars.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📭</div>
              <span>No recent announcements published</span>
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

        {/* ── ACHIEVEMENTS ─────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🏆 Regional Achievements</h2>
          </div>
          {achievements.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🌟</div>
              <span>No achievements published yet</span>
            </div>
          ) : (
            <div className="grid-3">
              {achievements.map((a, i) => (
                <AchievementCard key={a.id} achievement={a} index={i} animDelay={i * 80} />
              ))}
            </div>
          )}
        </section>

        {/* ── FOOTER ───────────────────────────────────────────── */}
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
