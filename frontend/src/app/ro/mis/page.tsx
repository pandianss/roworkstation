"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback } from "react";
import NavBar from "@/components/NavBar";
import SectionChart from "@/components/SectionChart";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Summary {
  total_deposits?: number;
  total_advances?: number;
  cd_ratio?: number;
  npa_pct?: number;
  [key: string]: unknown;
}

interface Performer {
  sol: number | string;
  name?: string;
  value: number;
}

interface TrendPoint {
  date: string;
  deposits?: number;
  advances?: number;
  [key: string]: unknown;
}

function Spinner() {
  return (
    <div
      style={{
        display: "inline-block",
        width: 28,
        height: 28,
        border: "3px solid rgba(255,255,255,0.1)",
        borderTopColor: "var(--color-primary-light)",
        borderRadius: "50%",
        animation: "spin 0.7s linear infinite",
      }}
    />
  );
}

function KpiCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div
      className="card"
      style={{
        padding: "1.4rem 1.5rem",
        background: "rgba(255,255,255,0.04)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255,255,255,0.09)",
        display: "flex",
        flexDirection: "column",
        gap: "0.4rem",
      }}
    >
      <div
        style={{
          fontSize: "0.68rem",
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--color-text-faint)",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "clamp(1.4rem,2.5vw,2rem)",
          fontWeight: 800,
          color: accent ?? "var(--color-text)",
          lineHeight: 1,
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function formatCr(v?: number) {
  if (v == null || isNaN(v)) return "—";
  return `₹ ${(v / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
}

export default function MISAnalyticsPage() {
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [performers, setPerformers] = useState<Performer[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [metric, setMetric] = useState("ADV");
  const [loading, setLoading] = useState(false);
  const [datesLoading, setDatesLoading] = useState(true);
  const [user, setUser] = useState<UserProfile | null>(null);

  // Fetch current user for NavBar
  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  // Load available dates
  useEffect(() => {
    fetch(`${API_BASE}/api/mis/available-dates`)
      .then((r) => (r.ok ? r.json() : { dates: [] }))
      .then((data) => {
        const d: string[] = data.dates ?? [];
        setDates(d);
        if (d.length) setSelectedDate(d[d.length - 1]);
      })
      .catch(() => setDates([]))
      .finally(() => setDatesLoading(false));
  }, []);

  // Load trend chart
  useEffect(() => {
    fetch(`${API_BASE}/api/mis/trend`)
      .then((r) => (r.ok ? r.json() : { trend: [] }))
      .then((data) => setTrend(data.trend ?? data.data ?? []))
      .catch(() => setTrend([]));
  }, []);

  // Load summary + performers on date / metric change
  const fetchData = useCallback(async () => {
    if (!selectedDate) return;
    setLoading(true);
    try {
      const [sumRes, perfRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/mis/summary?date=${selectedDate}`).then((r) =>
          r.ok ? r.json() : {}
        ),
        fetch(
          `${API_BASE}/api/mis/performers?date=${selectedDate}&metric=${metric}`
        ).then((r) => (r.ok ? r.json() : { performers: [] })),
      ]);
      if (sumRes.status === "fulfilled") setSummary(sumRes.value);
      if (perfRes.status === "fulfilled")
        setPerformers(perfRes.value.performers ?? []);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, [selectedDate, metric]);

  useEffect(() => {
    Promise.resolve().then(() => fetchData());
  }, [fetchData]);

  const top5    = [...performers].sort((a, b) => b.value - a.value).slice(0, 5);
  const bottom5 = [...performers].sort((a, b) => a.value - b.value).slice(0, 5);

  const METRICS = ["ADV", "TOTAL DEPOSITS", "CASA", "NPA %", "CD RATIO"];

  // Prepare trend data for SectionChart
  const trendChartData = trend.map((pt) => ({
    date: String(pt.date).slice(-5),
    "Total Deposits": pt.deposits ?? 0,
    "Total Advances": pt.advances ?? 0,
  }));

  return (
    <>
      <title>MIS Analytics | RO Workstation</title>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── Hero ────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              MIS Analytics · Live
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              MIS Analytics
            </h1>
            <p className={styles.heroSubtitle}>
              Explore date-wise deposits, advances, CD ratio, NPA and branch performers.
            </p>
          </div>
        </section>

        {/* ── Controls ────────────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "flex-end" }}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Report Date</label>
              {datesLoading ? (
                <Spinner />
              ) : (
                <select
                  className={styles.formSelect}
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  style={{ minWidth: 180 }}
                >
                  {dates.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                  {dates.length === 0 && <option value="">No dates available</option>}
                </select>
              )}
            </div>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Metric</label>
              <select
                className={styles.formSelect}
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                style={{ minWidth: 160 }}
              >
                {METRICS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            {loading && (
              <div style={{ paddingBottom: "0.25rem" }}>
                <Spinner />
              </div>
            )}
          </div>
        </section>

        {/* ── KPI Cards ───────────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-header">
            <h2>📊 Summary KPIs — {selectedDate || "—"}</h2>
          </div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
              <Spinner />
            </div>
          ) : (
            <div className="grid-4">
              <KpiCard label="Total Deposits"  value={formatCr(summary?.total_deposits as number)}  />
              <KpiCard label="Total Advances"  value={formatCr(summary?.total_advances as number)} accent="var(--color-accent-light)" />
              <KpiCard label="CD Ratio"        value={summary?.cd_ratio != null ? `${Number(summary.cd_ratio).toFixed(2)}%` : "—"} accent="var(--color-amber)" />
              <KpiCard label="NPA %"           value={summary?.npa_pct  != null ? `${Number(summary.npa_pct).toFixed(2)}%`  : "—"} accent="var(--color-red)" />
            </div>
          )}
        </section>

        <div className="divider" />

        {/* ── Trend Chart ──────────────────────────────────── */}
        {trendChartData.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>📈 Business Trend</h2>
            </div>
            <div className="card" style={{ padding: "1.5rem" }}>
              <SectionChart
                data={trendChartData}
                xKey="date"
                yKeys={["Total Deposits", "Total Advances"]}
                title="Regional Business Trend — Deposits & Advances"
                kind="area"
                height={280}
              />
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── Performers ──────────────────────────────────── */}
        {performers.length > 0 && (
          <section className="section">
            <div className="section-header">
              <h2>🏆 Performers — {metric}</h2>
            </div>
            <div className="grid-2">
              {/* Top 5 */}
              <div>
                <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--color-accent-light)", marginBottom: "0.75rem" }}>
                  ▲ Top 5 Branches
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {top5.map((p, i) => (
                    <div
                      key={i}
                      className="card"
                      style={{ padding: "0.85rem 1.1rem", display: "flex", alignItems: "center", gap: "1rem" }}
                    >
                      <div
                        style={{
                          width: 28, height: 28,
                          borderRadius: "50%",
                          background: i === 0 ? "hsl(38,95%,55%)" : i === 1 ? "hsl(215,25%,60%)" : "hsl(25,80%,50%)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontWeight: 800, fontSize: "0.78rem", color: "#000", flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: "0.88rem", color: "var(--color-text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {p.name ?? `SOL ${p.sol}`}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)" }}>SOL {p.sol}</div>
                      </div>
                      <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--color-accent-light)", whiteSpace: "nowrap" }}>
                        {formatCr(p.value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom 5 */}
              <div>
                <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--color-red)", marginBottom: "0.75rem" }}>
                  ▼ Bottom 5 Branches
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {bottom5.map((p, i) => (
                    <div
                      key={i}
                      className="card"
                      style={{ padding: "0.85rem 1.1rem", display: "flex", alignItems: "center", gap: "1rem" }}
                    >
                      <div
                        style={{
                          width: 28, height: 28, borderRadius: "50%",
                          background: "hsla(0,84%,60%,.15)",
                          border: "1px solid hsla(0,84%,60%,.25)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontWeight: 800, fontSize: "0.78rem", color: "var(--color-red)", flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: "0.88rem", color: "var(--color-text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {p.name ?? `SOL ${p.sol}`}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "var(--color-text-faint)" }}>SOL {p.sol}</div>
                      </div>
                      <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--color-red)", whiteSpace: "nowrap" }}>
                        {formatCr(p.value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {!loading && performers.length === 0 && selectedDate && (
          <div className={styles.emptyState} style={{ marginTop: "2rem" }}>
            <div className={styles.emptyIcon}>📊</div>
            <span>No performer data for {selectedDate}. Try selecting another date.</span>
          </div>
        )}

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>MIS Analytics · Dindigul RO</span>
          <span>Data from backend API</span>
        </footer>
      </main>
    </>
  );
}
