export const dynamic = "force-dynamic";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Anniversary Portal | RO Workstation",
  description: "Dindigul Regional Office branch founding anniversaries, staff birthdays, and upcoming retirement celebrations.",
};

import NavBar from "@/components/NavBar";
import { getMe } from "@/lib/api";
import styles from "@/styles/components.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface BranchAnniversary {
  sol?: number | string;
  name?: string;
  founded?: string;
  years?: number;
  date?: string;
}

interface StaffEvent {
  id?: string;
  staff_name?: string;
  name?: string;
  event_type?: string;
  type?: string;
  event_date?: string;
  date?: string;
  sol?: number | string;
  branch?: string;
}

interface RegistryEntry {
  sol?: number | string;
  name?: string;
  founded?: string;
  district?: string;
}

async function getData() {
  const [branchRes, staffRes, registryRes] = await Promise.allSettled([
    fetch(`${API_BASE}/api/anniversary/branches?days=30`, { cache: "no-store" }).then((r) =>
      r.ok ? r.json() : { branches: [] }
    ),
    fetch(`${API_BASE}/api/anniversary/staff?days=15`, { cache: "no-store" }).then((r) =>
      r.ok ? r.json() : { staff: [] }
    ),
    fetch(`${API_BASE}/api/anniversary/registry`, { cache: "no-store" }).then((r) =>
      r.ok ? r.json() : { registry: [] }
    ),
  ]);

  const branches: BranchAnniversary[] =
    branchRes.status === "fulfilled" ? (branchRes.value.branches ?? []) : [];
  const staff: StaffEvent[] =
    staffRes.status === "fulfilled" ? (staffRes.value.staff ?? []) : [];
  const registry: RegistryEntry[] =
    registryRes.status === "fulfilled" ? (registryRes.value.registry ?? []) : [];

  return { branches, staff, registry };
}

function eventColor(type?: string): string {
  if (!type) return "hsl(257,70%,65%)";
  const t = type.toUpperCase();
  if (t.includes("BIRTH")) return "hsl(38,95%,55%)";
  if (t.includes("RETIRE")) return "hsl(197,80%,50%)";
  return "hsl(257,70%,65%)";
}

function eventEmoji(type?: string): string {
  if (!type) return "🎉";
  const t = type.toUpperCase();
  if (t.includes("BIRTH")) return "🎂";
  if (t.includes("RETIRE")) return "🌟";
  return "🎊";
}

export default async function AnniversaryPage() {
  const [{ branches, staff, registry }, user] = await Promise.all([getData(), getMe()]);

  return (
    <>
      <NavBar activePage="ro" user={user} />

      <main className="container">
        {/* ── Hero ─────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{
              background:
                "linear-gradient(135deg, hsl(270,60%,22%) 0%, hsl(280,70%,45%) 100%)",
            }}
          >
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Anniversary Portal
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              🎉 Anniversary Portal
            </h1>
            <p className={styles.heroSubtitle}>
              Branch founding anniversaries, staff birthdays & upcoming retirement celebrations.
            </p>
          </div>
        </section>

        {/* ── Branch Anniversaries ─────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-header">
            <h2>🏛️ Upcoming Branch Anniversaries</h2>
            <span className="badge badge--blue">Next 30 days</span>
          </div>
          {branches.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🏛️</div>
              <span>No branch anniversaries in the next 30 days</span>
            </div>
          ) : (
            <div className="grid-3">
              {branches.map((b, i) => (
                <div
                  key={i}
                  className="card animate-fade-up"
                  style={{
                    padding: "1.5rem",
                    animationDelay: `${i * 50}ms`,
                    borderTop: "3px solid hsl(280,70%,60%)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.6rem",
                  }}
                >
                  <div style={{ fontSize: "2rem", lineHeight: 1 }}>🏛️</div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text)" }}>
                    {b.name ?? `SOL ${b.sol}`}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                    SOL {b.sol}
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
                    <span className="badge badge--blue">{b.date ?? b.founded}</span>
                    {b.years != null && (
                      <span
                        style={{
                          padding: "3px 10px",
                          borderRadius: 999,
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          background: "hsla(280,70%,60%,.15)",
                          color: "hsl(280,70%,75%)",
                          border: "1px solid hsla(280,70%,60%,.25)",
                        }}
                      >
                        {b.years} Year{b.years !== 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <div className="divider" />

        {/* ── Staff Events ─────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>👥 Staff Celebrations</h2>
            <span className="badge badge--amber">Next 15 days</span>
          </div>
          {staff.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🎂</div>
              <span>No staff events in the next 15 days</span>
            </div>
          ) : (
            <div className="grid-3">
              {staff.map((s, i) => {
                const type = s.event_type ?? s.type;
                const color = eventColor(type);
                return (
                  <div
                    key={i}
                    className="card animate-fade-up"
                    style={{
                      padding: "1.5rem",
                      animationDelay: `${i * 50}ms`,
                      borderTop: `3px solid ${color}`,
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.6rem",
                    }}
                  >
                    <div style={{ fontSize: "2rem", lineHeight: 1 }}>{eventEmoji(type)}</div>
                    <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text)" }}>
                      {s.staff_name ?? s.name ?? "Staff Member"}
                    </div>
                    <div
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "3px 10px",
                        borderRadius: 999,
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        background: `${color}22`,
                        color,
                        border: `1px solid ${color}44`,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        width: "fit-content",
                      }}
                    >
                      {type ?? "EVENT"}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "var(--color-text-muted)" }}>
                      📅 {s.event_date ?? s.date}
                    </div>
                    {(s.branch ?? s.sol) && (
                      <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)" }}>
                        {s.branch ?? `SOL ${s.sol}`}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <div className="divider" />

        {/* ── Founding Registry ────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>📋 Founding Registry</h2>
            <span className="badge badge--blue">{registry.length} Branches</span>
          </div>
          {registry.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📋</div>
              <span>Registry not available</span>
            </div>
          ) : (
            <div className="card" style={{ overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                    {["SOL", "Branch Name", "Founded", "District"].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: "0.85rem 1.25rem",
                          textAlign: "left",
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          color: "var(--color-text-faint)",
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {registry.map((r, i) => (
                    <tr
                      key={i}
                      style={{
                        borderBottom: "1px solid var(--color-border-subtle)",
                        background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                      }}
                    >
                      <td style={{ padding: "0.75rem 1.25rem", fontWeight: 700, color: "var(--color-primary-light)" }}>
                        {r.sol}
                      </td>
                      <td style={{ padding: "0.75rem 1.25rem", color: "var(--color-text)" }}>
                        {r.name}
                      </td>
                      <td style={{ padding: "0.75rem 1.25rem", color: "var(--color-text-muted)" }}>
                        {r.founded ?? "—"}
                      </td>
                      <td style={{ padding: "0.75rem 1.25rem", color: "var(--color-text-faint)" }}>
                        {r.district ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Anniversary Portal · Dindigul RO</span>
          <span>Data refreshes every request</span>
        </footer>
      </main>
    </>
  );
}
