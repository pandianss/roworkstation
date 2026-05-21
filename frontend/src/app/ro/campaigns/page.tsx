export const dynamic = "force-dynamic";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Campaign Tracker | RO Workstation",
  description: "Track active and completed regional business campaigns, targets, and progress for Dindigul branches.",
};

import NavBar from "@/components/NavBar";
import { getMe, getCampaigns, type Campaign } from "@/lib/api";
import styles from "@/styles/components.module.css";

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === "active")
    return <span className="badge badge--green">● Active</span>;
  if (s === "completed")
    return <span className="badge badge--blue">✓ Completed</span>;
  return <span className="badge">{status}</span>;
}

function daysRemaining(end_date: string): number {
  const now = new Date();
  const end = new Date(end_date);
  return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function progressPct(start: string, end: string): number {
  const s   = new Date(start).getTime();
  const e   = new Date(end).getTime();
  const now = Date.now();
  if (now <= s) return 0;
  if (now >= e) return 100;
  return Math.round(((now - s) / (e - s)) * 100);
}

export default async function CampaignsPage() {
  const [{ campaigns }, user] = await Promise.all([
    getCampaigns().catch(() => ({ campaigns: [] as Campaign[] })),
    getMe(),
  ]);

  const active    = campaigns.filter((c) => c.status?.toLowerCase() === "active");
  const completed = campaigns.filter((c) => c.status?.toLowerCase() !== "active");

  return (
    <>
      <NavBar activePage="ro" user={user} />

      <main className="container">
        {/* ── Hero ─────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{
              background: "linear-gradient(135deg, hsl(38,80%,20%) 0%, hsl(38,95%,40%) 100%)",
            }}
          >
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Campaigns
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              🚀 Campaign Tracker
            </h1>
            <p className={styles.heroSubtitle}>
              Track active and completed regional business campaigns, targets and progress.
            </p>
          </div>
        </section>

        {/* ── Active Campaigns ─────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-header">
            <h2>🟢 Active Campaigns</h2>
            <span className="badge badge--green">{active.length}</span>
          </div>

          {active.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📣</div>
              <span>No active campaigns at the moment</span>
            </div>
          ) : (
            <div className="grid-2">
              {active.map((c, i) => {
                const pct  = progressPct(c.start_date, c.end_date);
                const days = daysRemaining(c.end_date);
                return (
                  <div
                    key={i}
                    className="card animate-fade-up"
                    style={{
                      padding: 0,
                      animationDelay: `${i * 60}ms`,
                      overflow: "hidden",
                      position: "relative",
                    }}
                  >
                    {/* Gradient border strip */}
                    <div
                      style={{
                        height: 4,
                        background:
                          "linear-gradient(90deg, hsl(38,95%,55%), hsl(160,72%,50%))",
                      }}
                    />
                    <div style={{ padding: "1.4rem 1.5rem" }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          marginBottom: "0.75rem",
                          gap: "0.75rem",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 700,
                            fontSize: "1rem",
                            color: "var(--color-text)",
                          }}
                        >
                          {c.name}
                        </div>
                        <StatusBadge status={c.status} />
                      </div>

                      <div
                        style={{
                          fontSize: "0.78rem",
                          color: "var(--color-text-faint)",
                          marginBottom: "0.85rem",
                        }}
                      >
                        📅 {c.start_date} → {c.end_date}
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "1.5rem",
                          marginBottom: "1rem",
                          flexWrap: "wrap",
                        }}
                      >
                        <div>
                          <div style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-text-faint)", marginBottom: 2 }}>
                            Focus Metric
                          </div>
                          <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--color-amber)" }}>
                            {c.target_metric}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-text-faint)", marginBottom: 2 }}>
                            Target
                          </div>
                          <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--color-text)" }}>
                            ₹{c.target_value} Cr
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--color-text-faint)", marginBottom: 2 }}>
                            Ends In
                          </div>
                          <div style={{ fontWeight: 700, fontSize: "0.88rem", color: days < 7 ? "var(--color-red)" : "var(--color-accent-light)" }}>
                            {days > 0 ? `${days} days` : "Ended"}
                          </div>
                        </div>
                      </div>

                      {/* Progress bar */}
                      <div>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "0.72rem",
                            color: "var(--color-text-muted)",
                            marginBottom: "0.4rem",
                          }}
                        >
                          <span>Campaign Progress</span>
                          <span>{pct}%</span>
                        </div>
                        <div className="progress-track">
                          <div
                            className="progress-fill"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* ── Completed Campaigns ───────────────────────────── */}
        {completed.length > 0 && (
          <>
            <div className="divider" />
            <section className="section">
              <div className="section-header">
                <h2>✅ Completed Campaigns</h2>
                <span className="badge badge--blue">{completed.length}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {completed.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "0.85rem 1.25rem",
                      background: "var(--color-surface-2)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--color-border-subtle)",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "1rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--color-text-muted)" }}>
                        {c.name}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--color-text-faint)" }}>
                        {c.start_date} → {c.end_date} · {c.target_metric} · ₹{c.target_value} Cr
                      </div>
                    </div>
                    <StatusBadge status={c.status} />
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Campaign Tracker · Dindigul RO</span>
          <span>Data refreshes every request</span>
        </footer>
      </main>
    </>
  );
}
