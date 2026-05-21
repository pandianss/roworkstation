"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback } from "react";
import NavBar from "@/components/NavBar";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminStats {
  unit_count: number;
  staff_count: number;
  dept_count: number;
  mis_dates: number;
  mis_latest: string | null;
  ingested_files: number;
}

interface IngestedFile {
  filename: string;
  ingested_at: string;
}

interface MISFilesResponse {
  files: IngestedFile[];
  total_files: number;
  available_dates: string[];
  total_dates: number;
}

interface StaffMember {
  "Roll No": string;
  "Name (En)": string;
  "Branch SOL": string;
  Designation: string;
  Grade: string;
  Mobile: string;
  Gender: string;
  Active: boolean;
  DOB?: string;
  DOR?: string;
}

interface UnitRecord {
  Code: string;
  Name: string;
  Type: string | null;
  District: string | null;
  "Population Group": string | null;
  Head: string;
  "2nd Line": string;
  "Effective From": string | null;
  "Open Date": string | null;
  Active: boolean;
}

interface UserRecord {
  username: string;
  name: string;
  role: string;
  portal: string;
  dept: string;
  designation: string;
  grade: string;
  assigned_branches: string[];
}

// ── API helpers ────────────────────────────────────────────────────────────────

async function adminFetch(
  path: string,
  opts: RequestInit = {}
): Promise<Response> {
  const pwd = typeof window !== "undefined" ? sessionStorage.getItem("ro_admin_password") || "" : "";
  return fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Password": pwd,
      ...(opts.headers || {}),
    },
  });
}

async function verifyAdminPassword(password: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/admin/stats`, {
      headers: {
        "X-Admin-Password": password,
      },
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon: string;
  accent?: "blue" | "green" | "amber" | "red";
}) {
  const colors: Record<string, string> = {
    blue: "var(--color-primary-light)",
    green: "var(--color-accent-light)",
    amber: "var(--color-amber)",
    red: "var(--color-red)",
  };
  const c = colors[accent || "blue"];
  return (
    <div
      className="card"
      style={{
        padding: "1.25rem 1.5rem",
        display: "flex",
        gap: "1rem",
        alignItems: "center",
      }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: "var(--radius-md)",
          background: `${c}18`,
          border: `1px solid ${c}33`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "1.35rem",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div
          style={{
            fontSize: "1.6rem",
            fontWeight: 800,
            color: c,
            lineHeight: 1,
            letterSpacing: "-0.02em",
          }}
        >
          {value}
        </div>
        <div className="eyebrow" style={{ marginTop: 4 }}>
          {label}
        </div>
      </div>
    </div>
  );
}

function SyncButton({
  label,
  icon,
  onSync,
}: {
  label: string;
  icon: string;
  onSync: () => Promise<{ message: string }>;
}) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handle() {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const r = await onSync();
      setResult(r.message);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        padding: "1.25rem 1.5rem",
        background: "var(--color-surface-2)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border-subtle)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "1.5rem" }}>{icon}</span>
          <div>
            <div style={{ fontWeight: 700, color: "var(--color-text)" }}>
              {label}
            </div>
            <div
              style={{ fontSize: "0.78rem", color: "var(--color-text-faint)" }}
            >
              Reads from /files/ directory
            </div>
          </div>
        </div>
        <button
          onClick={handle}
          disabled={loading}
          className={styles.btnPrimary}
          style={{ minWidth: 110, opacity: loading ? 0.7 : 1 }}
        >
          {loading ? "Syncing…" : "↻ Sync Now"}
        </button>
      </div>
      {result && (
        <div
          className={`${styles.alert} ${styles.alertSuccess}`}
          style={{ marginTop: "0.875rem" }}
        >
          ✅ {result}
        </div>
      )}
      {error && (
        <div
          className={`${styles.alert} ${styles.alertError}`}
          style={{ marginTop: "0.875rem" }}
        >
          ❌ {error}
        </div>
      )}
    </div>
  );
}

// ── Role badge ──────────────────────────────────────────────────────────────

function RoleBadge({ role }: { role: string }) {
  const map: Record<string, string> = {
    ADMIN: "badge--green",
    USER: "badge--blue",
    GUEST: "badge--amber",
  };
  return (
    <span className={`badge ${map[role] || ""}`}>{role}</span>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

type Tab = "overview" | "mis" | "masters" | "staff" | "users" | "units";

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [user, setUser] = useState<UserProfile | null>(null);

  // authentication state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  // overview
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // mis tab
  const [misFiles, setMisFiles] = useState<MISFilesResponse | null>(null);
  const [misLoading, setMisLoading] = useState(false);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [purgeDate, setPurgeDate] = useState("");

  // staff tab
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [staffQuery, setStaffQuery] = useState("");
  const [staffLoading, setStaffLoading] = useState(false);

  // users tab
  const [usersData, setUsersData] = useState<UserRecord[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // units tab
  const [units, setUnits] = useState<UnitRecord[]>([]);
  const [unitsQuery, setUnitsQuery] = useState("");
  const [unitsLoading, setUnitsLoading] = useState(false);

  // ── Effects ─────────────────────────────────────────────────────────────

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setUser(d))
      .catch(() => null);
  }, []);

  useEffect(() => {
    const stored = sessionStorage.getItem("ro_admin_password");
    if (stored) {
      verifyAdminPassword(stored).then((isValid) => {
        if (isValid) {
          setIsAuthenticated(true);
        } else {
          sessionStorage.removeItem("ro_admin_password");
          setIsAuthenticated(false);
        }
      });
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const r = await adminFetch("/api/admin/stats");
      if (r.ok) setStats(await r.json());
    } catch {
      /* ignore */
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (isAuthenticated === true) {
        loadStats();
      }
    });
  }, [loadStats, isAuthenticated]);

  const loadMisFiles = useCallback(async () => {
    setMisLoading(true);
    try {
      const r = await adminFetch("/api/admin/mis/files");
      if (r.ok) setMisFiles(await r.json());
    } catch {
      /* ignore */
    } finally {
      setMisLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (tab === "mis" && isAuthenticated === true) loadMisFiles();
    });
  }, [tab, loadMisFiles, isAuthenticated]);

  const loadStaff = useCallback(async () => {
    setStaffLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/master/staff`);
      if (r.ok) {
        const d = await r.json();
        setStaff(d.staff || []);
      }
    } catch {
      /* ignore */
    } finally {
      setStaffLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (tab === "staff" && isAuthenticated === true) loadStaff();
    });
  }, [tab, loadStaff, isAuthenticated]);

  const loadUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const r = await adminFetch("/api/admin/users");
      if (r.ok) {
        const d = await r.json();
        setUsersData(d.users || []);
      }
    } catch {
      /* ignore */
    } finally {
      setUsersLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (tab === "users" && isAuthenticated === true) loadUsers();
    });
  }, [tab, loadUsers, isAuthenticated]);

  const loadUnits = useCallback(async () => {
    setUnitsLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/master/units`);
      if (r.ok) {
        const d = await r.json();
        setUnits(d.units || []);
      }
    } catch {
      /* ignore */
    } finally {
      setUnitsLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (tab === "units" && isAuthenticated === true) loadUnits();
    });
  }, [tab, loadUnits, isAuthenticated]);


  // ── Actions ──────────────────────────────────────────────────────────────

  async function triggerIngest() {
    setIngestLoading(true);
    setIngestResult(null);
    setIngestError(null);
    try {
      const r = await adminFetch("/api/admin/mis/ingest", { method: "POST" });
      const d = await r.json();
      if (r.ok) {
        setIngestResult(d.message);
        loadMisFiles();
        loadStats();
      } else {
        setIngestError(d.detail || "Ingest failed");
      }
    } catch (e: unknown) {
      setIngestError(e instanceof Error ? e.message : "Network error");
    } finally {
      setIngestLoading(false);
    }
  }

  async function deleteFileLog(filename: string) {
    if (!confirm(`Remove ingest log for "${filename}"? The data remains in DB.`)) return;
    const r = await adminFetch(
      `/api/admin/mis/files/${encodeURIComponent(filename)}`,
      { method: "DELETE" }
    );
    if (r.ok) loadMisFiles();
  }

  async function purgeByDate() {
    if (!purgeDate) return;
    if (!confirm(`Permanently delete ALL MIS records for ${purgeDate}?`)) return;
    const r = await adminFetch(`/api/admin/mis/purge-date/${purgeDate}`, {
      method: "DELETE",
    });
    const d = await r.json();
    if (r.ok) {
      setIngestResult(d.message);
      loadMisFiles();
      loadStats();
    } else {
      setIngestError(d.detail);
    }
  }

  async function syncMasters(type: "staff" | "units" | "departments" | "all") {
    const r = await adminFetch(`/api/admin/master/sync/${type}`, {
      method: "POST",
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "Sync failed");
    loadStats();
    return d;
  }

  // ── Filtered staff ────────────────────────────────────────────────────────
  const filteredStaff = staff.filter((s) => {
    const q = staffQuery.toLowerCase();
    return (
      !q ||
      s["Name (En)"]?.toLowerCase().includes(q) ||
      s["Roll No"]?.toString().includes(q) ||
      s["Branch SOL"]?.toString().includes(q) ||
      s.Designation?.toLowerCase().includes(q)
    );
  });

  // ── Filtered units ────────────────────────────────────────────────────────
  const filteredUnits = units.filter((u) => {
    const q = unitsQuery.toLowerCase();
    return (
      !q ||
      u.Code?.toLowerCase().includes(q) ||
      u.Name?.toLowerCase().includes(q) ||
      u.Type?.toLowerCase().includes(q) ||
      u.District?.toLowerCase().includes(q) ||
      u["Population Group"]?.toLowerCase().includes(q) ||
      u.Head?.toLowerCase().includes(q) ||
      u["2nd Line"]?.toLowerCase().includes(q)
    );
  });

  const TABS: { id: Tab; label: string; icon: string }[] = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "mis",      label: "MIS Ingestion", icon: "📥" },
    { id: "masters",  label: "Master Sync", icon: "🔄" },
    { id: "staff",    label: "Staff Roster", icon: "👥" },
    { id: "users",    label: "Users & Access", icon: "🔐" },
    { id: "units",    label: "Units Master", icon: "🏦" },
  ];

  // ── Password Submit Action ──────────────────────────────────────────────────
  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setVerifying(true);
    setAuthError(null);
    const success = await verifyAdminPassword(passwordInput);
    if (success) {
      sessionStorage.setItem("ro_admin_password", passwordInput);
      setIsAuthenticated(true);
    } else {
      setAuthError("Incorrect administrator password. Please try again.");
    }
    setVerifying(false);
  }

  // ── Render ────────────────────────────────────────────────────────────────
  if (isAuthenticated === null) {
    return (
      <>
        <title>Admin Console | RO Workstation</title>
        <NavBar activePage="ro" user={user ?? undefined} />
        <main className="container" style={{ minHeight: "80vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ textAlign: "center" }}>
            <span className="spin" style={{ fontSize: "2.4rem", color: "var(--color-primary-light)", marginBottom: "1rem" }}>⟳</span>
            <div style={{ color: "var(--color-text-muted)", fontSize: "0.95rem", marginTop: "1rem" }}>Verifying access...</div>
          </div>
        </main>
      </>
    );
  }

  if (isAuthenticated === false) {
    return (
      <>
        <title>Admin Console Login | RO Workstation</title>
        <NavBar activePage="ro" user={user ?? undefined} />
        <main className="container" style={{ minHeight: "75vh", display: "flex", alignItems: "center", justifyContent: "center", paddingTop: "2rem", paddingBottom: "4rem" }}>
          <div
            className="card animate-fade-up"
            style={{
              width: "100%",
              maxWidth: "460px",
              padding: "2.5rem",
              background: "var(--gradient-card)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--color-border-subtle)",
              boxShadow: "var(--shadow-lg), var(--shadow-glow)",
            }}
          >
            <div style={{ textAlign: "center", marginBottom: "2rem" }}>
              <div
                style={{
                  width: "60px",
                  height: "60px",
                  borderRadius: "var(--radius-md)",
                  background: "hsla(257, 70%, 65%, 0.12)",
                  border: "1px solid hsla(257, 70%, 65%, 0.25)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.8rem",
                  margin: "0 auto 1.25rem",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.1)",
                }}
              >
                🔐
              </div>
              <h2 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--color-text)", marginBottom: "0.5rem" }}>
                Admin Console Access
              </h2>
              <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", lineHeight: 1.5 }}>
                This area contains sensitive master data and system sync operations. Enter the administrator password to unlock.
              </p>
            </div>

            <form onSubmit={handlePasswordSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel} htmlFor="admin-password">
                  Administrator Password
                </label>
                <input
                  id="admin-password"
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="••••••••"
                  className={styles.formInput}
                  autoFocus
                  style={{
                    fontSize: "1rem",
                    padding: "0.75rem 1rem",
                    textAlign: "center",
                    letterSpacing: passwordInput ? "0.3em" : "normal",
                  }}
                />
              </div>

              {authError && (
                <div
                  className={`${styles.alert} ${styles.alertError}`}
                  style={{ fontSize: "0.825rem", display: "flex", alignItems: "center", gap: "0.5rem" }}
                >
                  ❌ {authError}
                </div>
              )}

              <button
                type="submit"
                disabled={verifying || !passwordInput}
                className={styles.btnPrimary}
                style={{
                  width: "100%",
                  padding: "0.8rem",
                  fontSize: "0.9rem",
                  fontWeight: 700,
                  opacity: (verifying || !passwordInput) ? 0.7 : 1,
                  cursor: (verifying || !passwordInput) ? "not-allowed" : "pointer",
                }}
              >
                {verifying ? (
                  <>
                    <span className="spin" style={{ marginRight: "0.5rem" }}>⟳</span> Verifying…
                  </>
                ) : (
                  "Unlock Console"
                )}
              </button>
            </form>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <title>Admin Console | RO Workstation</title>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin { animation: spin 0.8s linear infinite; display: inline-block; }
        table { border-collapse: collapse; width: 100%; }
        th, td { padding: 0.6rem 0.875rem; text-align: left; border-bottom: 1px solid var(--color-border-subtle); font-size: 0.82rem; }
        th { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-text-faint); background: var(--color-surface-2); }
        tr:hover td { background: rgba(255,255,255,0.02); }
        td { color: var(--color-text-muted); }
        td:first-child { color: var(--color-text); font-weight: 600; }
      `}</style>

      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── HERO ──────────────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div
            className={styles.hero}
            style={{
              background:
                "linear-gradient(135deg, hsl(257,60%,18%) 0%, hsl(257,70%,38%) 100%)",
              marginBottom: "2rem",
              position: "relative",
            }}
          >
            {/* Lock Console Button */}
            <button
              onClick={() => {
                sessionStorage.removeItem("ro_admin_password");
                setIsAuthenticated(false);
                setPasswordInput("");
              }}
              style={{
                position: "absolute",
                top: "1.5rem",
                right: "1.5rem",
                padding: "0.5rem 1rem",
                background: "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                borderRadius: "var(--radius-md)",
                color: "#fff",
                fontWeight: 600,
                fontSize: "0.8rem",
                cursor: "pointer",
                transition: "all var(--duration-fast) var(--ease-out)",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                zIndex: 10,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.18)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.35)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.08)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.15)";
                e.currentTarget.style.transform = "none";
              }}
            >
              🔒 Lock Console
            </button>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              System Administration
            </div>
            <div className={styles.heroEyebrow}>Admin Console</div>
            <h1 className={styles.heroTitle}>Master Management</h1>
            <p className={styles.heroSubtitle}>
              Manage MIS ingestion, sync master data, view staff roster and
              user access controls.
            </p>
          </div>
        </section>

        {/* ── TAB BAR ───────────────────────────────────────────────── */}
        <div className={styles.tabBar} style={{ marginBottom: "2rem" }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`${styles.tab} ${tab === t.id ? styles.tabActive : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* ══════════════════════════════════════════════════════════════
            TAB: OVERVIEW
        ══════════════════════════════════════════════════════════════ */}
        {tab === "overview" && (
          <>
            {statsLoading ? (
              <div className={styles.emptyState}>
                <span className="spin">⟳</span> Loading stats…
              </div>
            ) : stats ? (
              <>
                <div className="section-header">
                  <h2>📊 System Overview</h2>
                </div>
                <div className="grid-3" style={{ marginBottom: "2rem" }}>
                  <StatCard icon="🏦" label="Branch Units" value={stats.unit_count} accent="blue" />
                  <StatCard icon="👤" label="Staff Records" value={stats.staff_count} accent="green" />
                  <StatCard icon="🏢" label="Departments" value={stats.dept_count} accent="amber" />
                  <StatCard icon="📅" label="MIS Dates in DB" value={stats.mis_dates} accent="blue" />
                  <StatCard icon="📁" label="Ingested Files" value={stats.ingested_files} accent="green" />
                  <StatCard
                    icon="🕐"
                    label="Latest MIS Date"
                    value={stats.mis_latest ?? "No data"}
                    accent="amber"
                  />
                </div>

                <div
                  className="card"
                  style={{ padding: "1.5rem", marginTop: "0.5rem" }}
                >
                  <h3 style={{ marginBottom: "1rem" }}>Quick Actions</h3>
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                    }}
                  >
                    {[
                      { label: "→ MIS Ingestion", t: "mis" as Tab },
                      { label: "→ Master Sync", t: "masters" as Tab },
                      { label: "→ Staff Roster", t: "staff" as Tab },
                      { label: "→ Units Master", t: "units" as Tab },
                      { label: "→ Users & Access", t: "users" as Tab },
                    ].map((a) => (
                      <button
                        key={a.t}
                        onClick={() => setTab(a.t)}
                        style={{
                          padding: "0.55rem 1.25rem",
                          background: "var(--color-surface-3)",
                          border: "1px solid var(--color-border)",
                          borderRadius: "var(--radius-md)",
                          color: "var(--color-primary-light)",
                          fontWeight: 600,
                          fontSize: "0.85rem",
                          cursor: "pointer",
                        }}
                      >
                        {a.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>⚠️</div>
                <span>Could not load admin stats. Check server connection.</span>
              </div>
            )}
          </>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB: MIS INGESTION
        ══════════════════════════════════════════════════════════════ */}
        {tab === "mis" && (
          <>
            {/* Ingest trigger */}
            <div className="section-header">
              <h2>📥 MIS Ingestion</h2>
            </div>
            <div className="card" style={{ padding: "1.5rem", marginBottom: "1.5rem" }}>
              <h3 style={{ marginBottom: "0.5rem" }}>Trigger Ingestion</h3>
              <p style={{ fontSize: "0.85rem", marginBottom: "1.25rem" }}>
                Scans the <code style={{ background: "var(--color-surface-3)", padding: "1px 6px", borderRadius: 4 }}>files/</code> directory for new MIS Excel files and ingests them into the database.
                Files already ingested are skipped unless forced.
              </p>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <button
                  className={styles.btnPrimary}
                  onClick={triggerIngest}
                  disabled={ingestLoading}
                  style={{ opacity: ingestLoading ? 0.7 : 1 }}
                >
                  {ingestLoading ? "⟳ Ingesting…" : "📥 Ingest New Files"}
                </button>
              </div>
              {ingestResult && (
                <div className={`${styles.alert} ${styles.alertSuccess}`} style={{ marginTop: "1rem" }}>
                  ✅ {ingestResult}
                </div>
              )}
              {ingestError && (
                <div className={`${styles.alert} ${styles.alertError}`} style={{ marginTop: "1rem" }}>
                  ❌ {ingestError}
                </div>
              )}
            </div>

            {/* Purge by date */}
            <div className="card" style={{ padding: "1.5rem", marginBottom: "1.5rem", borderColor: "hsla(0,84%,60%,.2)" }}>
              <h3 style={{ marginBottom: "0.5rem", color: "var(--color-red)" }}>⚠ Purge Records by Date</h3>
              <p style={{ fontSize: "0.85rem", marginBottom: "1.25rem" }}>
                Permanently delete all MIS records for a specific reporting date. Use this to correct bad data before re-ingesting.
              </p>
              <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                <input
                  type="date"
                  value={purgeDate}
                  onChange={(e) => setPurgeDate(e.target.value)}
                  className={styles.formInput}
                  style={{ maxWidth: 200 }}
                />
                <button
                  onClick={purgeByDate}
                  disabled={!purgeDate}
                  style={{
                    padding: "0.65rem 1.25rem",
                    background: "hsla(0,84%,60%,.15)",
                    border: "1px solid hsla(0,84%,60%,.3)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--color-red)",
                    fontWeight: 700,
                    cursor: purgeDate ? "pointer" : "not-allowed",
                    fontSize: "0.875rem",
                    opacity: purgeDate ? 1 : 0.5,
                  }}
                >
                  🗑 Purge Date
                </button>
              </div>
            </div>

            {/* Ingested files table */}
            <div className="section-header" style={{ marginTop: "0.5rem" }}>
              <h3>📁 Ingested Files Log</h3>
              {misFiles && (
                <span className="badge badge--blue">
                  {misFiles.total_files} files · {misFiles.total_dates} dates
                </span>
              )}
            </div>

            {misLoading ? (
              <div className={styles.emptyState}><span className="spin">⟳</span> Loading…</div>
            ) : misFiles && misFiles.files.length > 0 ? (
              <div className="card" style={{ overflow: "hidden" }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Filename</th>
                      <th>Ingested At</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {misFiles.files.map((f, i) => (
                      <tr key={f.filename}>
                        <td style={{ color: "var(--color-text-faint)", width: 40 }}>{i + 1}</td>
                        <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{f.filename}</td>
                        <td>{f.ingested_at?.replace("T", " ").substring(0, 19)}</td>
                        <td>
                          <button
                            onClick={() => deleteFileLog(f.filename)}
                            style={{
                              padding: "3px 10px",
                              background: "hsla(0,84%,60%,.1)",
                              border: "1px solid hsla(0,84%,60%,.2)",
                              borderRadius: 6,
                              color: "var(--color-red)",
                              fontSize: "0.75rem",
                              cursor: "pointer",
                              fontWeight: 600,
                            }}
                          >
                            Remove Log
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>📭</div>
                <span>No files have been ingested yet. Place MIS Excel files in the <code>files/</code> directory and trigger ingestion.</span>
              </div>
            )}

            {/* Available dates summary */}
            {misFiles && misFiles.available_dates.length > 0 && (
              <div style={{ marginTop: "1.5rem" }}>
                <div className="section-header"><h3>📅 Available Reporting Dates</h3></div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {misFiles.available_dates.map((d) => (
                    <span
                      key={d}
                      className="badge badge--blue"
                      style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}
                    >
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB: MASTER SYNC
        ══════════════════════════════════════════════════════════════ */}
        {tab === "masters" && (
          <>
            <div className="section-header">
              <h2>🔄 Master Data Sync</h2>
            </div>
            <p style={{ color: "var(--color-text-muted)", marginBottom: "1.75rem", fontSize: "0.9rem" }}>
              Sync master tables from CSV/Excel source files in the <code style={{ background: "var(--color-surface-3)", padding: "1px 6px", borderRadius: 4 }}>files/</code> directory.
              Each sync upserts existing records and deactivates removed entries.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SyncButton
                icon="🏦"
                label="Sync Branch Units (branches.csv)"
                onSync={() => syncMasters("units")}
              />
              <SyncButton
                icon="👤"
                label="Sync Staff Roster (Staff.csv / Staff Details*.xlsx)"
                onSync={() => syncMasters("staff")}
              />
              <SyncButton
                icon="🏢"
                label="Sync Departments (departments.csv)"
                onSync={() => syncMasters("departments")}
              />

              <div className="divider" />

              <SyncButton
                icon="🚀"
                label="Sync All Masters (units → staff → departments)"
                onSync={() => syncMasters("all")}
              />
            </div>

            <div
              className="card"
              style={{
                padding: "1.25rem 1.5rem",
                marginTop: "2rem",
                borderLeft: "3px solid var(--color-amber)",
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: "0.4rem", color: "var(--color-amber)" }}>
                📋 Expected file names
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.82rem", color: "var(--color-text-muted)" }}>
                {[
                  ["branches.csv", "Branch unit master (code, nameEn, nameHi, nameTa, district, type…)"],
                  ["Staff.csv", "Staff base data (Roll No, Name, Designation, Grade, Br Cd…)"],
                  ["Staff Details*.xlsx", "Optional: Excel override for staff data (same columns)"],
                  ["StfData.csv", "Optional seed: DOB/DOR override for staff"],
                  ["departments.csv", "Dept master (dept_code, dept_en, dept_hi, dept_ta, email)"],
                ].map(([f, d]) => (
                  <div key={f} style={{ gridColumn: "span 1" }}>
                    <code
                      style={{
                        display: "block",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.78rem",
                        color: "var(--color-primary-light)",
                        marginBottom: 2,
                      }}
                    >
                      {f}
                    </code>
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-faint)" }}>{d}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB: STAFF ROSTER
        ══════════════════════════════════════════════════════════════ */}
        {tab === "staff" && (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1.5rem",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <h2 style={{ margin: 0 }}>👥 Staff Roster</h2>
              {staff.length > 0 && (
                <span className="badge badge--blue">{staff.length} staff members</span>
              )}
            </div>

            <div className={styles.searchWrapper} style={{ marginBottom: "1.25rem" }}>
              <span className={styles.searchIcon}>🔍</span>
              <input
                type="text"
                placeholder="Search by name, roll no, SOL or designation…"
                value={staffQuery}
                onChange={(e) => setStaffQuery(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            {staffLoading ? (
              <div className={styles.emptyState}><span className="spin">⟳</span> Loading staff…</div>
            ) : filteredStaff.length === 0 ? (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>👤</div>
                <span>{staffQuery ? "No staff match your search." : "No staff data. Run a staff sync first."}</span>
              </div>
            ) : (
              <div className="card" style={{ overflow: "hidden" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Roll No</th>
                      <th>Name</th>
                      <th>Branch SOL</th>
                      <th>Designation</th>
                      <th>Grade</th>
                      <th>Mobile</th>
                      <th>DOB</th>
                      <th>DOR</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStaff.map((s) => (
                      <tr key={s["Roll No"]}>
                        <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                          {s["Roll No"]}
                        </td>
                        <td style={{ color: "var(--color-text)", fontWeight: 600 }}>
                          {s["Name (En)"]}
                        </td>
                        <td>
                          <span className="badge badge--blue" style={{ fontSize: "0.68rem" }}>
                            {s["Branch SOL"]}
                          </span>
                        </td>
                        <td>{s.Designation}</td>
                        <td>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--color-amber)" }}>
                            {s.Grade}
                          </span>
                        </td>
                        <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>{s.Mobile || "—"}</td>
                        <td style={{ fontSize: "0.75rem" }}>{s.DOB || "—"}</td>
                        <td style={{ fontSize: "0.75rem" }}>{s.DOR || "—"}</td>
                        <td>
                          <span
                            className={`badge ${s.Active ? "badge--green" : "badge--red"}`}
                            style={{ fontSize: "0.65rem" }}
                          >
                            {s.Active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB: USERS & ACCESS
        ══════════════════════════════════════════════════════════════ */}
        {tab === "users" && (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1.5rem",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <h2 style={{ margin: 0 }}>🔐 Users & Access</h2>
              {usersData.length > 0 && (
                <span className="badge badge--blue">{usersData.length} users</span>
              )}
            </div>

            {usersLoading ? (
              <div className={styles.emptyState}><span className="spin">⟳</span> Loading users…</div>
            ) : usersData.length === 0 ? (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>🔐</div>
                <span>No user data. Ensure staff master is synced.</span>
              </div>
            ) : (
              <>
                {/* Role summary pills */}
                <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
                  {(["ADMIN", "USER", "GUEST"] as const).map((role) => {
                    const count = usersData.filter((u) => u.role === role).length;
                    return (
                      <div
                        key={role}
                        className="card"
                        style={{ padding: "0.875rem 1.25rem", display: "flex", gap: "0.75rem", alignItems: "center" }}
                      >
                        <RoleBadge role={role} />
                        <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>{count}</span>
                      </div>
                    );
                  })}
                </div>

                <div className="card" style={{ overflow: "hidden" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Username</th>
                        <th>Name</th>
                        <th>Role</th>
                        <th>Portal</th>
                        <th>Designation</th>
                        <th>Grade</th>
                        <th>Department</th>
                        <th>Assigned Branches</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usersData.map((u) => (
                        <tr key={u.username}>
                          <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                            {u.username}
                          </td>
                          <td style={{ color: "var(--color-text)", fontWeight: 600 }}>{u.name}</td>
                          <td><RoleBadge role={u.role} /></td>
                          <td>
                            <span className="badge badge--blue" style={{ fontSize: "0.65rem", textTransform: "capitalize" }}>
                              {u.portal}
                            </span>
                          </td>
                          <td>{u.designation || "—"}</td>
                          <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--color-amber)" }}>
                            {u.grade || "—"}
                          </td>
                          <td>{u.dept || "ALL"}</td>
                          <td>
                            {u.assigned_branches?.length > 0 ? (
                              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                                {u.assigned_branches.slice(0, 3).map((b) => (
                                  <span key={b} className="badge badge--blue" style={{ fontSize: "0.62rem" }}>{b}</span>
                                ))}
                                {u.assigned_branches.length > 3 && (
                                  <span className="badge badge--amber" style={{ fontSize: "0.62rem" }}>
                                    +{u.assigned_branches.length - 3} more
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span style={{ color: "var(--color-text-faint)" }}>—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB: UNITS MASTER
        ══════════════════════════════════════════════════════════════ */}
        {tab === "units" && (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1.5rem",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <h2 style={{ margin: 0 }}>🏦 Units Master</h2>
              {units.length > 0 && (
                <span className="badge badge--blue">{units.length} units</span>
              )}
            </div>

            <div className={styles.searchWrapper} style={{ marginBottom: "1.25rem" }}>
              <span className={styles.searchIcon}>🔍</span>
              <input
                type="text"
                placeholder="Search by code, name, type, district or population group…"
                value={unitsQuery}
                onChange={(e) => setUnitsQuery(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            {unitsLoading ? (
              <div className={styles.emptyState}><span className="spin">⟳</span> Loading units…</div>
            ) : filteredUnits.length === 0 ? (
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>🏦</div>
                <span>{unitsQuery ? "No units match your search." : "No unit data. Run a unit sync first."}</span>
              </div>
            ) : (
              <div className="card" style={{ overflow: "hidden" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Name</th>
                      <th>Type</th>
                      <th>District</th>
                      <th>Population Group</th>
                      <th>Head Officer</th>
                      <th>2nd Line</th>
                      <th>Open Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUnits.map((u) => (
                      <tr key={u.Code}>
                        <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                          {u.Code}
                        </td>
                        <td style={{ color: "var(--color-text)", fontWeight: 600 }}>
                          {u.Name}
                        </td>
                        <td>{u.Type || "—"}</td>
                        <td>{u.District || "—"}</td>
                        <td>
                          <span style={{ fontSize: "0.75rem", color: "var(--color-primary-light)" }}>
                            {u["Population Group"] || "—"}
                          </span>
                        </td>
                        <td>{u.Head || "—"}</td>
                        <td>{u["2nd Line"] || "—"}</td>
                        <td style={{ fontSize: "0.75rem" }}>{u["Open Date"] || "—"}</td>
                        <td>
                          <span
                            className={`badge ${u.Active ? "badge--green" : "badge--red"}`}
                            style={{ fontSize: "0.65rem" }}
                          >
                            {u.Active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        <div style={{ height: "3rem" }} />
      </main>
    </>
  );
}
