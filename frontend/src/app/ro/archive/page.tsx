"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback } from "react";
import NavBar from "@/components/NavBar";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Circular {
  id: string;
  ref_no?: string;
  number?: string;
  subject?: string;
  title?: string;
  date?: string;
  dept?: string;
  category?: string;
}

const DEPTS = ["ALL", "CREDIT", "RECOVERY", "HR", "IT", "COMPLIANCE", "OPERATIONS", "ACCOUNTS", "VIGILANCE"];

function Spinner() {
  return (
    <div style={{ display: "inline-block", width: 24, height: 24, border: "3px solid rgba(255,255,255,0.1)", borderTopColor: "var(--color-primary-light)", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
  );
}

export default function ArchivePage() {
  const [query, setQuery]         = useState("");
  const [dept, setDept]           = useState("ALL");
  const [circulars, setCirculars] = useState<Circular[]>([]);
  const [loading, setLoading]     = useState(false);
  const [expanded, setExpanded]   = useState<string | null>(null);
  const [page, setPage]           = useState(1);
  const [user, setUser]           = useState<UserProfile | null>(null);

  const PER_PAGE = 15;

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  const search = useCallback(async () => {
    setLoading(true);
    setPage(1);
    try {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (dept && dept !== "ALL") params.set("dept", dept);
      const res = await fetch(`${API_BASE}/api/circulars/search?${params}`);
      if (res.ok) {
        const data = await res.json();
        setCirculars(data.circulars ?? data.data ?? []);
      } else {
        setCirculars([]);
      }
    } catch {
      setCirculars([]);
    } finally {
      setLoading(false);
    }
  }, [query, dept]);

  // Load on mount and when dept changes
  useEffect(() => {
    Promise.resolve().then(() => search());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dept]);

  const paginated = circulars.slice(0, page * PER_PAGE);
  const hasMore   = circulars.length > page * PER_PAGE;

  return (
    <>
      <title>Central Archive | RO Workstation</title>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── Hero ─────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{ background: "linear-gradient(135deg, hsl(197,80%,18%) 0%, hsl(197,80%,38%) 100%)" }}
          >
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Central Archive
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle} style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)" }}>
              🗄️ Central Archive
            </h1>
            <p className={styles.heroSubtitle}>
              Search and browse all regional circulars, notices and departmental communications.
            </p>
          </div>
        </section>

        {/* ── Search Controls ──────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
            <div className={styles.formGroup} style={{ flex: 1, minWidth: 240 }}>
              <label className={styles.formLabel}>Search</label>
              <div className={styles.searchWrapper}>
                <span className={styles.searchIcon}>🔍</span>
                <input
                  className={styles.searchInput}
                  type="text"
                  placeholder="Ref no, subject, keyword…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && search()}
                />
              </div>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Department</label>
              <select
                className={styles.formSelect}
                value={dept}
                onChange={(e) => setDept(e.target.value)}
              >
                {DEPTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <button className={styles.btnPrimary} onClick={search}>
              Search
            </button>
            {loading && <Spinner />}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--color-text-faint)", marginTop: "0.75rem" }}>
            {loading ? "Searching…" : `${circulars.length} circular${circulars.length !== 1 ? "s" : ""} found`}
          </div>
        </section>

        {/* ── Results ──────────────────────────────────────── */}
        <section className="section" style={{ paddingTop: 0 }}>
          {circulars.length === 0 && !loading ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🗄️</div>
              <span>No circulars found. Try a different search or department.</span>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {paginated.map((c) => {
                  const isExp = expanded === c.id;
                  const refNo = c.ref_no ?? c.number ?? "—";
                  const subj  = c.subject ?? c.title ?? "Untitled";
                  return (
                    <div
                      key={c.id}
                      className="card animate-fade-up"
                      style={{
                        padding: "1rem 1.25rem",
                        cursor: "pointer",
                        borderLeft: "3px solid var(--color-primary-light)",
                        transition: "all 0.2s",
                      }}
                      onClick={() => setExpanded(isExp ? null : c.id)}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.35rem" }}>
                            <span style={{ fontWeight: 700, fontSize: "0.72rem", color: "var(--color-primary-light)", letterSpacing: "0.04em" }}>
                              {refNo}
                            </span>
                            {c.dept && <span className="badge badge--blue">{c.dept}</span>}
                            {c.category && <span className="badge badge--green">{c.category}</span>}
                          </div>
                          <div
                            style={{
                              fontWeight: 600,
                              fontSize: "0.88rem",
                              color: "var(--color-text)",
                              overflow: isExp ? "visible" : "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: isExp ? "normal" : "nowrap",
                              lineHeight: 1.5,
                            }}
                          >
                            {subj}
                          </div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexShrink: 0 }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--color-text-faint)" }}>
                            {c.date ?? "—"}
                          </span>
                          <span style={{ color: "var(--color-text-faint)", fontSize: "0.8rem" }}>
                            {isExp ? "▲" : "▼"}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {hasMore && (
                <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
                  <button
                    className={styles.btnPrimary}
                    onClick={() => setPage((p) => p + 1)}
                    style={{ opacity: 0.85 }}
                  >
                    Load more
                  </button>
                </div>
              )}
            </>
          )}
        </section>

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Central Archive · Dindigul RO</span>
          <span>Search results from API</span>
        </footer>
      </main>
    </>
  );
}
