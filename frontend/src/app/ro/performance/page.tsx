"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback } from "react";
import NavBar from "@/components/NavBar";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface BranchPerf {
  sol: number | string;
  name?: string;
  value: number;
  rank?: number;
}

const METRICS = [
  { key: "ADV",             label: "Advances" },
  { key: "TOTAL DEPOSITS",  label: "Total Deposits" },
  { key: "CASA",            label: "CASA" },
  { key: "NPA %",           label: "NPA %" },
  { key: "CD RATIO",        label: "CD Ratio" },
];

function formatVal(v: number, metric: string): string {
  if (metric === "NPA %" || metric === "CD RATIO") return `${v.toFixed(2)}%`;
  return `₹ ${(v / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
}

function Spinner() {
  return (
    <div style={{ display: "inline-block", width: 24, height: 24, border: "3px solid rgba(255,255,255,0.1)", borderTopColor: "var(--color-primary-light)", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
  );
}

function RankBadge({ rank }: { rank: number }) {
  const colors: Record<number, string> = {
    1: "hsl(38,95%,55%)",
    2: "hsl(215,25%,65%)",
    3: "hsl(25,80%,50%)",
  };
  return (
    <div
      style={{
        width: 32,
        height: 32,
        borderRadius: "50%",
        background: colors[rank] ?? "var(--color-surface-3)",
        border: `1px solid ${colors[rank] ?? "var(--color-border)"}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 800,
        fontSize: "0.78rem",
        color: rank <= 3 ? "#000" : "var(--color-text-muted)",
        flexShrink: 0,
      }}
    >
      {rank}
    </div>
  );
}

export default function PerformancePage() {
  const [metric, setMetric]       = useState("ADV");
  const [branches, setBranches]   = useState<BranchPerf[]>([]);
  const [loading, setLoading]     = useState(false);
  const [user, setUser]           = useState<UserProfile | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  const fetchPerf = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/performance/branches?metric=${encodeURIComponent(metric)}`
      );
      if (res.ok) {
        const data = await res.json();
        setBranches(data.branches ?? data.data ?? []);
      } else {
        setBranches([]);
      }
    } catch {
      setBranches([]);
    } finally {
      setLoading(false);
    }
  }, [metric]);

  useEffect(() => {
    Promise.resolve().then(() => fetchPerf());
  }, [fetchPerf]);

  const sorted  = [...branches].sort((a, b) => b.value - a.value);
  const top5    = sorted.slice(0, 5);
  const bottom5 = [...branches].sort((a, b) => a.value - b.value).slice(0, 5);
  const maxVal  = sorted[0]?.value ?? 1;
  const metricLabel = METRICS.find((m) => m.key === metric)?.label ?? metric;

  return (
    <>
      <title>Performance Rankings | RO Workstation</title>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── Hero ─────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{ background: "linear-gradient(135deg, hsl(158,76%,18%) 0%, hsl(158,60%,36%) 100%)" }}
          >
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Branch Performance
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              🏆 Performance Rankings
            </h1>
            <p className={styles.heroSubtitle}>
              Ranked branch performance across key business metrics.
            </p>
          </div>
        </section>

        {/* ── Metric Selector ───────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
            {METRICS.map((m) => (
              <button
                key={m.key}
                onClick={() => setMetric(m.key)}
                className={`${styles.tab} ${metric === m.key ? styles.tabActive : ""}`}
              >
                {m.label}
              </button>
            ))}
            {loading && <Spinner />}
          </div>
        </section>

        {/* ── Top 5 / Bottom 5 ─────────────────────────────── */}
        {!loading && branches.length > 0 && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="grid-2">
              {/* Top 5 */}
              <div>
                <div className="section-header">
                  <h3 style={{ color: "var(--color-accent-light)", fontSize: "1rem" }}>
                    ▲ Top 5 — {metricLabel}
                  </h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  {top5.map((b, i) => (
                    <div
                      key={i}
                      className="card animate-fade-up"
                      style={{
                        padding: "0.9rem 1.1rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.85rem",
                        animationDelay: `${i * 50}ms`,
                      }}
                    >
                      <RankBadge rank={i + 1} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--color-text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {b.name ?? `SOL ${b.sol}`}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--color-text-faint)" }}>SOL {b.sol}</div>
                      </div>
                      <div style={{ fontWeight: 800, fontSize: "0.9rem", color: "var(--color-accent-light)", whiteSpace: "nowrap" }}>
                        {formatVal(b.value, metric)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom 5 */}
              <div>
                <div className="section-header">
                  <h3 style={{ color: "var(--color-red)", fontSize: "1rem" }}>
                    ▼ Bottom 5 — {metricLabel}
                  </h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  {bottom5.map((b, i) => (
                    <div
                      key={i}
                      className="card animate-fade-up"
                      style={{
                        padding: "0.9rem 1.1rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.85rem",
                        animationDelay: `${i * 50}ms`,
                        borderLeft: "3px solid var(--color-red)",
                      }}
                    >
                      <div style={{ width: 32, height: 32, borderRadius: "50%", background: "hsla(0,84%,60%,.12)", border: "1px solid hsla(0,84%,60%,.25)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "0.78rem", color: "var(--color-red)", flexShrink: 0 }}>
                        {i + 1}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--color-text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {b.name ?? `SOL ${b.sol}`}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--color-text-faint)" }}>SOL {b.sol}</div>
                      </div>
                      <div style={{ fontWeight: 800, fontSize: "0.9rem", color: "var(--color-red)", whiteSpace: "nowrap" }}>
                        {formatVal(b.value, metric)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── Full Ranked Table ────────────────────────────── */}
        {!loading && sorted.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>📋 Full Rankings — {metricLabel}</h2>
              <span className="badge badge--blue">{sorted.length} Branches</span>
            </div>
            <div className="card" style={{ overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                    {["Rank", "SOL", "Branch", metricLabel, "Bar"].map((h) => (
                      <th key={h} style={{ padding: "0.85rem 1.1rem", textAlign: "left", fontSize: "0.68rem", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-text-faint)" }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((b, i) => {
                    const pct = maxVal > 0 ? (b.value / maxVal) * 100 : 0;
                    return (
                      <tr key={i} style={{ borderBottom: "1px solid var(--color-border-subtle)", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)" }}>
                        <td style={{ padding: "0.75rem 1.1rem" }}>
                          <span style={{ fontWeight: 700, color: i < 3 ? "var(--color-amber)" : "var(--color-text-faint)", fontSize: "0.85rem" }}>
                            #{i + 1}
                          </span>
                        </td>
                        <td style={{ padding: "0.75rem 1.1rem", fontWeight: 700, color: "var(--color-primary-light)" }}>{b.sol}</td>
                        <td style={{ padding: "0.75rem 1.1rem", color: "var(--color-text)" }}>{b.name ?? "—"}</td>
                        <td style={{ padding: "0.75rem 1.1rem", fontWeight: 700, color: "var(--color-text)", whiteSpace: "nowrap" }}>{formatVal(b.value, metric)}</td>
                        <td style={{ padding: "0.75rem 1.1rem", minWidth: 120 }}>
                          <div className="progress-track">
                            <div className="progress-fill" style={{ width: `${pct}%` }} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
            <Spinner />
          </div>
        )}

        {!loading && branches.length === 0 && (
          <div className={styles.emptyState} style={{ marginTop: "2rem" }}>
            <div className={styles.emptyIcon}>🏆</div>
            <span>No performance data available for this metric.</span>
          </div>
        )}

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Performance Rankings · Dindigul RO</span>
          <span>Data from API</span>
        </footer>
      </main>
    </>
  );
}
