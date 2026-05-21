"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import NavBar from "@/components/NavBar";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Visit {
  id: string;
  branch_name: string;
  branch_code: string;
  visit_date: string;
  visit_type: string;
  status: string;
  notes?: string;
  created_at?: string;
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

export default function BranchVisitsPage() {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [formData, setFormData] = useState({
    branch_name: "",
    branch_code: "",
    visit_date: "",
    visit_type: "ROUTINE",
    notes: "",
  });

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  // Load visits
  useEffect(() => {
    fetch(`${API_BASE}/api/visits`)
      .then((r) => (r.ok ? r.json() : { visits: [] }))
      .then((data) => setVisits(data.visits ?? []))
      .catch(() => setVisits([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/visits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        const newVisit = await res.json();
        setVisits([newVisit, ...visits]);
        setShowForm(false);
        setFormData({ branch_name: "", branch_code: "", visit_date: "", visit_type: "ROUTINE", notes: "" });
      }
    } catch (err) {
      console.error("Failed to create visit:", err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "SCHEDULED": return "hsl(217,91%,55%)";
      case "COMPLETED": return "hsl(158,76%,46%)";
      case "CANCELLED": return "hsl(0,84%,60%)";
      default: return "var(--color-text-faint)";
    }
  };

  const sortedVisits = [...visits].sort((a, b) => 
    new Date(b.visit_date).getTime() - new Date(a.visit_date).getTime()
  );

  return (
    <>
      <title>Branch Inspection Visits | RO Workstation</title>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── Hero ────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Branch Visits · Management
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle}>Branch Inspection Visits</h1>
            <p className={styles.heroSubtitle}>
              Schedule, track, and manage RO branch inspection visits and follow-ups.
            </p>
            <button
              onClick={() => setShowForm(!showForm)}
              style={{
                marginTop: "1.5rem",
                padding: "0.75rem 1.5rem",
                background: "var(--color-primary-light)",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "0.9rem",
              }}
            >
              {showForm ? "Cancel" : "+ Schedule New Visit"}
            </button>
          </div>
        </section>

        {/* ── Form ─────────────────────────────────────────── */}
        {showForm && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="card" style={{ padding: "1.5rem" }}>
              <h3 style={{ marginBottom: "1rem", color: "var(--color-text)" }}>Schedule New Visit</h3>
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Branch Name</label>
                  <input
                    type="text"
                    className={styles.formInput}
                    value={formData.branch_name}
                    onChange={(e) => setFormData({ ...formData, branch_name: e.target.value })}
                    required
                    placeholder="Enter branch name"
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Branch Code (SOL)</label>
                  <input
                    type="text"
                    className={styles.formInput}
                    value={formData.branch_code}
                    onChange={(e) => setFormData({ ...formData, branch_code: e.target.value })}
                    required
                    placeholder="Enter branch code"
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Visit Date</label>
                  <input
                    type="date"
                    className={styles.formInput}
                    value={formData.visit_date}
                    onChange={(e) => setFormData({ ...formData, visit_date: e.target.value })}
                    required
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Visit Type</label>
                  <select
                    className={styles.formSelect}
                    value={formData.visit_type}
                    onChange={(e) => setFormData({ ...formData, visit_type: e.target.value })}
                  >
                    <option value="ROUTINE">Routine Inspection</option>
                    <option value="SPECIAL">Special Inspection</option>
                    <option value="FOLLOW_UP">Follow-up Visit</option>
                    <option value="AUDIT">Audit Visit</option>
                  </select>
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Notes (Optional)</label>
                  <textarea
                    className={styles.formInput}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    placeholder="Additional notes or objectives"
                  />
                </div>
                <button
                  type="submit"
                  style={{
                    padding: "0.75rem 1.5rem",
                    background: "var(--color-primary-light)",
                    color: "#fff",
                    border: "none",
                    borderRadius: "8px",
                    fontWeight: 600,
                    cursor: "pointer",
                    fontSize: "0.9rem",
                    alignSelf: "flex-start",
                  }}
                >
                  Schedule Visit
                </button>
              </form>
            </div>
          </section>
        )}

        <div className="divider" />

        {/* ── Visits List ──────────────────────────────────── */}
        <section className="section">
          <div className="section-header">
            <h2>📋 Scheduled Visits</h2>
          </div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
              <Spinner />
            </div>
          ) : sortedVisits.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📋</div>
              <span>No visits scheduled yet. Click &quot;Schedule New Visit&quot; to get started.</span>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {sortedVisits.map((visit) => (
                <div
                  key={visit.id}
                  className="card"
                  style={{
                    padding: "1.25rem 1.5rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.75rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
                    <div>
                      <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--color-text)", marginBottom: "0.25rem" }}>
                        {visit.branch_name}
                      </h3>
                      <div style={{ fontSize: "0.85rem", color: "var(--color-text-faint)" }}>
                        SOL {visit.branch_code} · {visit.visit_type}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <span
                        style={{
                          padding: "0.35rem 0.75rem",
                          borderRadius: "20px",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          background: `${getStatusColor(visit.status)}20`,
                          color: getStatusColor(visit.status),
                          border: `1px solid ${getStatusColor(visit.status)}40`,
                        }}
                      >
                        {visit.status}
                      </span>
                      <span style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
                        {new Date(visit.visit_date).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>
                  {visit.notes && (
                    <div style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", lineHeight: 1.5, paddingTop: "0.5rem", borderTop: "1px solid var(--color-border-subtle)" }}>
                      <strong>Notes:</strong> {visit.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Branch Visits · Dindigul RO</span>
          <span>Visit Management System</span>
        </footer>
      </main>
    </>
  );
}
