"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import NavBar from "@/components/NavBar";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WIZARDS = [
  {
    id: "office_note",
    title: "Office Note",
    description: "Generate internal office notes for communications and records",
    icon: "📝",
    color: "hsl(217,91%,55%)",
  },
  {
    id: "appreciation_letter",
    title: "Appreciation Letter",
    description: "Create appreciation letters for staff performance recognition",
    icon: "🏆",
    color: "hsl(38,95%,55%)",
  },
  {
    id: "explanation_letter",
    title: "Explanation Letter",
    description: "Draft explanation letters for clarifications and responses",
    icon: "📄",
    color: "hsl(197,80%,50%)",
  },
  {
    id: "branch_visit_report",
    title: "Branch Visit Report",
    description: "Generate reports after branch inspection visits",
    icon: "🔍",
    color: "hsl(158,76%,46%)",
  },
  {
    id: "circular",
    title: "Circular/Notice",
    description: "Create official circulars and notices for distribution",
    icon: "📢",
    color: "hsl(280,70%,65%)",
  },
  {
    id: "performance_appreciation",
    title: "Performance Appreciation",
    description: "Recognize and appreciate outstanding branch performance",
    icon: "⭐",
    color: "hsl(25,80%,50%)",
  },
  {
    id: "campaign_poster",
    title: "Campaign Poster",
    description: "Generate promotional materials for business campaigns",
    icon: "🚀",
    color: "hsl(0,84%,60%)",
  },
  {
    id: "budget_communication",
    title: "Budget Communication",
    description: "Communicate budget allocations and financial information",
    icon: "💰",
    color: "hsl(215,25%,60%)",
  },
];

export default function WizardsPage() {
  const [selectedWizard, setSelectedWizard] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [generatedDoc, setGeneratedDoc] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  const handleWizardSelect = (wizardId: string) => {
    setSelectedWizard(wizardId);
    setFormData({});
    setGeneratedDoc(null);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleGenerate = async () => {
    if (!selectedWizard) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/wizards/${selectedWizard}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedDoc(data.document || data.html);
      }
    } catch (err) {
      console.error("Failed to generate document:", err);
    } finally {
      setLoading(false);
    }
  };

  const getFormFields = (wizardId: string) => {
    switch (wizardId) {
      case "office_note":
        return [
          { key: "to", label: "To", type: "text", placeholder: "Recipient name/department" },
          { key: "subject", label: "Subject", type: "text", placeholder: "Subject of the note" },
          { key: "content", label: "Content", type: "textarea", placeholder: "Main content of the note" },
        ];
      case "appreciation_letter":
        return [
          { key: "recipient_name", label: "Recipient Name", type: "text", placeholder: "Staff member name" },
          { key: "achievement", label: "Achievement", type: "textarea", placeholder: "Describe the achievement" },
          { key: "date", label: "Date", type: "date" },
        ];
      case "explanation_letter":
        return [
          { key: "recipient", label: "To", type: "text", placeholder: "Recipient name" },
          { key: "subject", label: "Subject", type: "text", placeholder: "Subject of explanation" },
          { key: "explanation", label: "Explanation", type: "textarea", placeholder: "Detailed explanation" },
        ];
      case "branch_visit_report":
        return [
          { key: "branch_name", label: "Branch Name", type: "text", placeholder: "Branch visited" },
          { key: "visit_date", label: "Visit Date", type: "date" },
          { key: "findings", label: "Findings", type: "textarea", placeholder: "Key findings from visit" },
          { key: "recommendations", label: "Recommendations", type: "textarea", placeholder: "Recommendations" },
        ];
      case "circular":
        return [
          { key: "circular_number", label: "Circular Number", type: "text", placeholder: "e.g., CIRC/2024/001" },
          { key: "subject", label: "Subject", type: "text", placeholder: "Subject of circular" },
          { key: "content", label: "Content", type: "textarea", placeholder: "Circular content" },
          { key: "date", label: "Date", type: "date" },
        ];
      case "performance_appreciation":
        return [
          { key: "branch_name", label: "Branch Name", type: "text", placeholder: "Branch name" },
          { key: "metric", label: "Metric", type: "text", placeholder: "e.g., Deposits, Advances" },
          { key: "achievement", label: "Achievement", type: "textarea", placeholder: "Describe the achievement" },
        ];
      case "campaign_poster":
        return [
          { key: "campaign_name", label: "Campaign Name", type: "text", placeholder: "Campaign title" },
          { key: "target", label: "Target", type: "text", placeholder: "Campaign target" },
          { key: "message", label: "Key Message", type: "textarea", placeholder: "Main message for poster" },
        ];
      case "budget_communication":
        return [
          { key: "department", label: "Department", type: "text", placeholder: "Department name" },
          { key: "allocation", label: "Allocation", type: "text", placeholder: "Budget amount" },
          { key: "notes", label: "Notes", type: "textarea", placeholder: "Additional notes" },
        ];
      default:
        return [];
    }
  };

  const currentWizard = WIZARDS.find((w) => w.id === selectedWizard);
  const formFields = selectedWizard ? getFormFields(selectedWizard) : [];

  return (
    <>
      <title>Document Generation Wizards | RO Workstation</title>
      <NavBar activePage="ro" user={user ?? undefined} />

      <main className="container">
        {/* ── Hero ────────────────────────────────────────── */}
        <section style={{ paddingTop: "2rem" }}>
          <div className={styles.hero}>
            <div className={styles.heroBadge}>
              <span className={styles.heroDot} />
              Document Wizards · Generation
            </div>
            <div className={styles.heroEyebrow}>Dindigul Regional Office</div>
            <h1 className={styles.heroTitle}>Document Generation Wizards</h1>
            <p className={styles.heroSubtitle}>
              Quick and easy document generation for notes, letters, reports, and communications.
            </p>
          </div>
        </section>

        {!selectedWizard ? (
          <>
            <div className="divider" />

            {/* ── Wizard Selection ───────────────────────────── */}
            <section className="section">
              <div className="section-header">
                <h2>📝 Select a Document Type</h2>
              </div>
              <div className="grid-3">
                {WIZARDS.map((wizard) => (
                  <div
                    key={wizard.id}
                    onClick={() => handleWizardSelect(wizard.id)}
                    className="card animate-fade-up"
                    style={{
                      padding: "1.5rem",
                      cursor: "pointer",
                      borderTop: `3px solid ${wizard.color}`,
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.65rem",
                      transition: "transform 0.2s, box-shadow 0.2s",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = "translateY(-4px)";
                      e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.15)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "translateY(0)";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    <div style={{ fontSize: "2rem", lineHeight: 1 }}>{wizard.icon}</div>
                    <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text)" }}>
                      {wizard.title}
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--color-text-muted)", lineHeight: 1.5 }}>
                      {wizard.description}
                    </div>
                    <div style={{ fontSize: "0.75rem", fontWeight: 600, color: wizard.color, marginTop: "auto" }}>
                      Select →
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        ) : (
          <>
            <div className="divider" />

            {/* ── Wizard Form ───────────────────────────────── */}
            <section className="section">
              <div className="section-header">
                <button
                  onClick={() => setSelectedWizard(null)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--color-text-muted)",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  ← Back to all wizards
                </button>
                <h2>
                  {currentWizard?.icon} {currentWizard?.title}
                </h2>
              </div>

              <div className="grid-2">
                {/* Form */}
                <div className="card" style={{ padding: "1.5rem" }}>
                  <h3 style={{ marginBottom: "1rem", color: "var(--color-text)" }}>Enter Details</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    {formFields.map((field) => (
                      <div key={field.key} className={styles.formGroup}>
                        <label className={styles.formLabel}>{field.label}</label>
                        {field.type === "textarea" ? (
                          <textarea
                            className={styles.formInput}
                            rows={4}
                            placeholder={field.placeholder}
                            value={formData[field.key] || ""}
                            onChange={(e) => handleInputChange(field.key, e.target.value)}
                          />
                        ) : (
                          <input
                            type={field.type}
                            className={styles.formInput}
                            placeholder={field.placeholder}
                            value={formData[field.key] || ""}
                            onChange={(e) => handleInputChange(field.key, e.target.value)}
                          />
                        )}
                      </div>
                    ))}
                    <button
                      onClick={handleGenerate}
                      disabled={loading}
                      style={{
                        padding: "0.75rem 1.5rem",
                        background: loading ? "var(--color-text-muted)" : currentWizard?.color,
                        color: "#fff",
                        border: "none",
                        borderRadius: "8px",
                        fontWeight: 600,
                        cursor: loading ? "not-allowed" : "pointer",
                        fontSize: "0.9rem",
                        opacity: loading ? 0.7 : 1,
                      }}
                    >
                      {loading ? "Generating..." : "Generate Document"}
                    </button>
                  </div>
                </div>

                {/* Preview */}
                <div className="card" style={{ padding: "1.5rem" }}>
                  <h3 style={{ marginBottom: "1rem", color: "var(--color-text)" }}>Preview</h3>
                  {generatedDoc ? (
                    <div>
                      <div
                        dangerouslySetInnerHTML={{ __html: generatedDoc }}
                        style={{
                          background: "var(--color-surface-2)",
                          padding: "1.5rem",
                          borderRadius: "8px",
                          minHeight: "300px",
                          fontSize: "0.9rem",
                          lineHeight: 1.6,
                        }}
                      />
                      <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
                        <button
                          onClick={() => window.print()}
                          style={{
                            flex: 1,
                            padding: "0.65rem 1rem",
                            background: "var(--color-surface-3)",
                            color: "var(--color-text)",
                            border: "1px solid var(--color-border)",
                            borderRadius: "8px",
                            fontWeight: 600,
                            cursor: "pointer",
                            fontSize: "0.85rem",
                          }}
                        >
                          🖨️ Print
                        </button>
                        <button
                          onClick={() => {
                            const blob = new Blob([generatedDoc], { type: "text/html" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `${currentWizard?.id ?? "document"}.html`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          style={{
                            flex: 1,
                            padding: "0.65rem 1rem",
                            background: currentWizard?.color,
                            color: "#fff",
                            border: "none",
                            borderRadius: "8px",
                            fontWeight: 600,
                            cursor: "pointer",
                            fontSize: "0.85rem",
                          }}
                        >
                          ⬇️ Download
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      style={{
                        background: "var(--color-surface-2)",
                        padding: "2rem",
                        borderRadius: "8px",
                        minHeight: "300px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--color-text-faint)",
                        fontSize: "0.9rem",
                      }}
                    >
                      Fill in the form and click &quot;Generate Document&quot; to see the preview
                    </div>
                  )}
                </div>
              </div>
            </section>
          </>
        )}

        <footer style={{ borderTop: "1px solid var(--color-border-subtle)", paddingBlock: "2rem", marginTop: "2rem", fontSize: "0.78rem", color: "var(--color-text-faint)", display: "flex", justifyContent: "space-between" }}>
          <span>Document Wizards · Dindigul RO</span>
          <span>Automated Document Generation</span>
        </footer>
      </main>
    </>
  );
}
