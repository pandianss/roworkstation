import { redirect } from "next/navigation";
import type { Metadata } from "next";

export const dynamic = "force-dynamic"; // must run per-request so getMe() resolves the OS user

export const metadata: Metadata = {
  title: "Dindigul Regional Office | Guest Portal",
  description: "Explore the Dindigul Regional Office network, organizational setup, and branch directory.",
};

import {
  getUnits, getDepartments, getCirculars, getAchievements, getMe,
} from "@/lib/api";

import NavBar          from "@/components/NavBar";
import BranchDirectory from "@/components/BranchDirectory";
import DemographicsPanel from "@/components/DemographicsPanel";
import AnnouncementCard from "@/components/AnnouncementCard";
import AchievementCard  from "@/components/AchievementCard";

import styles from "@/styles/components.module.css";

async function getData() {
  const [unitsRes, deptsRes, circularsRes, achievementsRes] =
    await Promise.allSettled([
      getUnits(),
      getDepartments(),
      getCirculars(),
      getAchievements(),
    ]);

  const units        = unitsRes.status        === "fulfilled" ? unitsRes.value.units               : [];
  const depts        = deptsRes.status        === "fulfilled" ? deptsRes.value.departments         : [];
  const circulars    = circularsRes.status    === "fulfilled" ? circularsRes.value.circulars        : [];
  const achievements = achievementsRes.status === "fulfilled" ? achievementsRes.value.achievements : [];

  return { units, depts, circulars, achievements };
}

export default async function GuestPortalPage() {
  // Resolve user — redirect authenticated staff to their portal
  const user = await getMe();
  if (user.portal === "ro") redirect("/ro");
  if (user.portal === "branch" && user.assigned_branches.length > 0) {
    redirect(`/branch/${user.assigned_branches[0]}`);
  }

  const { units, depts, circulars, achievements } = await getData();

  const activeDepts = depts.filter((d) => d.Active);
  const activeUnits = units.filter((u) => u.Type !== "REGIONAL OFFICE" && u.Active);
  const roUnit      = units.find((u) => u.Type === "REGIONAL OFFICE");
  const rmName      = roUnit?.Head ?? "The Regional Manager";

  return (
    <>
      <NavBar activePage="guest" />

      <main className="container">
        {/* ── HERO ─────────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Public Portal · Read-Only
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle}>Regional Business Portal</h1>
            <p className={styles.heroSubtitle}>
              Transparency and Excellence in Banking. Public overview of regional
              network, organisational structure, and key announcements.
            </p>
            <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
              <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "0.75rem 1.25rem", backdropFilter: "blur(8px)" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "rgba(255,255,255,0.6)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Network</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>{activeUnits.length} Active Branches</div>
              </div>
              <div style={{ background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "0.75rem 1.25rem", backdropFilter: "blur(8px)" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "rgba(255,255,255,0.6)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Departments</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>{activeDepts.length} Departments</div>
              </div>
            </div>
          </div>
        </section>

        <div className="divider" />

        {/* ── DEMOGRAPHICS ─────────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>🌐 Network Overview</h2>
          </div>
          <DemographicsPanel units={units} />
        </section>

        <div className="divider" />

        {/* ── ORGANISATION ─────────────────────────────────────── */}
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
            <h2>🔍 Branch Directory</h2>
          </div>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
            Find branch location details and designated unit authorities.
          </p>
          <BranchDirectory units={units} />
        </section>

        <div className="divider" />

        {/* ── ANNOUNCEMENTS ────────────────────────────────────── */}
        {circulars.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>📢 Announcements &amp; Notices</h2>
            </div>
            <div className="grid-3">
              {circulars.slice(0, 6).map((c, i) => (
                <AnnouncementCard key={c.id} circular={c} animDelay={i * 60} />
              ))}
            </div>
          </section>
        )}

        {achievements.length > 0 && (
          <>
            <div className="divider" />
            <section className="section">
              <div className="section-header">
                <h2>🏆 Regional Achievements</h2>
              </div>
              <div className="grid-3">
                {achievements.map((a, i) => (
                  <AchievementCard key={a.id} achievement={a} index={i} animDelay={i * 80} />
                ))}
              </div>
            </section>
          </>
        )}

        {/* ── FOOTER ───────────────────────────────────────────── */}
        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ fontWeight: 700, color: "var(--color-text)" }}>RO Workstation</div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>
              Dindigul Regional Office · Public Portal
            </div>
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}>
            Powered by FastAPI + Next.js
          </div>
        </footer>
      </main>
    </>
  );
}
