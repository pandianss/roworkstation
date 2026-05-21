export const dynamic = "force-dynamic";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Field Guardian | RO Workstation",
  description: "Track, escalate, and resolve field issues and actions items across Dindigul Regional Office branches.",
};

import NavBar from "@/components/NavBar";
import { getMe } from "@/lib/api";
import styles from "@/styles/components.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FollowUp {
  id?: string;
  branch?: string;
  sol?: number | string;
  category?: string;
  status?: string;
  priority?: string;
  details?: string;
  description?: string;
  timestamp?: string;
  created_at?: string;
  updated_at?: string;
}

async function getFollowUps(): Promise<FollowUp[]> {
  try {
    const res = await fetch(`${API_BASE}/api/guardian/followups`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.followups ?? data.data ?? [];
  } catch {
    return [];
  }
}

function statusStyle(status?: string): React.CSSProperties {
  const s = (status ?? "").toUpperCase();
  if (s === "RESOLVED")  return { background: "hsla(158,76%,36%,.12)", color: "var(--color-accent-light)", border: "1px solid hsla(158,76%,36%,.25)" };
  if (s === "ESCALATED") return { background: "hsla(0,84%,60%,.12)",   color: "var(--color-red)",          border: "1px solid hsla(0,84%,60%,.25)" };
  /* PENDING / default */
  return { background: "hsla(38,95%,55%,.12)", color: "var(--color-amber)", border: "1px solid hsla(38,95%,55%,.25)" };
}

function priorityStyle(p?: string): React.CSSProperties {
  const pr = (p ?? "").toUpperCase();
  if (pr === "P1") return { background: "hsla(0,84%,60%,.15)",   color: "var(--color-red)",          border: "1px solid hsla(0,84%,60%,.25)" };
  if (pr === "P2") return { background: "hsla(38,95%,55%,.15)",  color: "var(--color-amber)",         border: "1px solid hsla(38,95%,55%,.25)" };
  if (pr === "P3") return { background: "hsla(217,91%,55%,.15)", color: "var(--color-primary-light)", border: "1px solid hsla(217,91%,55%,.25)" };
  /* P4 / default */
  return { background: "rgba(255,255,255,.07)", color: "var(--color-text-faint)", border: "1px solid rgba(255,255,255,.1)" };
}

function cardBorderColor(status?: string): string {
  const s = (status ?? "").toUpperCase();
  if (s === "RESOLVED")  return "var(--color-accent-light)";
  if (s === "ESCALATED") return "var(--color-red)";
  return "var(--color-amber)";
}

function timeAgo(ts?: string): string {
  if (!ts) return "—";
  try {
    const d = new Date(ts);
    const diff = Date.now() - d.getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(mins  / 60);
    const days  = Math.floor(hours / 24);
    if (days  > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (mins  > 0) return `${mins}m ago`;
    return "Just now";
  } catch {
    return ts;
  }
}

export default async function GuardianPage() {
  const [followUps, user] = await Promise.all([getFollowUps(), getMe()]);

  const pending   = followUps.filter((f) => (f.status ?? "").toUpperCase() === "PENDING");
  const escalated = followUps.filter((f) => (f.status ?? "").toUpperCase() === "ESCALATED");
  const resolved  = followUps.filter((f) => (f.status ?? "").toUpperCase() === "RESOLVED");

  return (
    <>
      <NavBar activePage="ro" user={user} />

      <main className="container">
        {/* ── Hero ─────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{ background: "linear-gradient(135deg, hsl(0,60%,18%) 0%, hsl(0,72%,36%) 100%)" }}
          >
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Field Guardian
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              🛡️ Field Guardian
            </h1>
            <p className={styles.heroSubtitle}>
              Track, escalate and resolve field issues across branches.
            </p>
            {/* Stats strip */}
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "1.25rem" }}>
              {[
                { label: "Pending",   count: pending.length,   color: "var(--color-amber)" },
                { label: "Escalated", count: escalated.length, color: "var(--color-red)" },
                { label: "Resolved",  count: resolved.length,  color: "var(--color-accent-light)" },
              ].map((s) => (
                <div key={s.label} style={{ background: "rgba(255,255,255,0.11)", borderRadius: 10, padding: "0.6rem 1rem", backdropFilter: "blur(8px)" }}>
                  <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "rgba(255,255,255,0.55)", letterSpacing: "0.1em", textTransform: "uppercase" }}>{s.label}</div>
                  <div style={{ fontWeight: 800, color: s.color, fontSize: "1.2rem", lineHeight: 1.2 }}>{s.count}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Follow-up Cards ───────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-header">
            <h2>📋 All Follow-ups</h2>
            <span className="badge badge--blue">{followUps.length} Total</span>
          </div>

          {followUps.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🛡️</div>
              <span>No follow-ups found. All clear!</span>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {followUps.map((f, i) => (
                <div
                  key={f.id ?? i}
                  className="card animate-fade-up"
                  style={{
                    padding: "1.25rem 1.5rem",
                    borderLeft: `4px solid ${cardBorderColor(f.status)}`,
                    animationDelay: `${i * 40}ms`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text)", marginBottom: "0.2rem" }}>
                        {f.branch ?? (f.sol != null ? `SOL ${f.sol}` : "Unknown Branch")}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--color-text-faint)" }}>
                        📂 {f.category ?? "General"} · 🕒 {timeAgo(f.timestamp ?? f.created_at)}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", flexShrink: 0 }}>
                      {/* Priority badge */}
                      {f.priority && (
                        <span
                          style={{
                            ...priorityStyle(f.priority),
                            padding: "3px 10px",
                            borderRadius: 999,
                            fontSize: "0.68rem",
                            fontWeight: 700,
                            letterSpacing: "0.06em",
                            textTransform: "uppercase",
                          }}
                        >
                          {f.priority}
                        </span>
                      )}
                      {/* Status badge */}
                      <span
                        style={{
                          ...statusStyle(f.status),
                          padding: "3px 10px",
                          borderRadius: 999,
                          fontSize: "0.68rem",
                          fontWeight: 700,
                          letterSpacing: "0.06em",
                          textTransform: "uppercase",
                        }}
                      >
                        {f.status ?? "PENDING"}
                      </span>
                    </div>
                  </div>

                  {(f.details ?? f.description) && (
                    <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", lineHeight: 1.55, margin: 0 }}>
                      {f.details ?? f.description}
                    </p>
                  )}

                  {f.updated_at && (
                    <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)", marginTop: "0.5rem" }}>
                      Last updated: {timeAgo(f.updated_at)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Field Guardian · Dindigul RO</span>
          <span>Live data · Refreshes each visit</span>
        </footer>
      </main>
    </>
  );
}
