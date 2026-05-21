"use client";

import { useState, useTransition } from "react";
import type { Department } from "@/lib/api";
import styles from "@/styles/components.module.css";

interface CoordinationFormProps {
  sol: string;
  departments: Department[];
}

export default function CoordinationForm({ sol, departments }: CoordinationFormProps) {
  const [isPending, startTransition] = useTransition();
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const activeDepts = departments.filter((d) => d.Active);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload = {
      sender_unit: sol,
      receiver_dept: fd.get("dept"),
      subject: fd.get("subject"),
      message: fd.get("message"),
      priority: fd.get("priority"),
      sender_name: "Branch Manager",
    };

    startTransition(async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/communications`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Server error");
        setSuccess(true);
        (e.target as HTMLFormElement).reset();
      } catch {
        setError("Failed to submit request. Please try again.");
      }
    });
  }

  return (
    <div>
      {success && (
        <div className={`${styles.alert} ${styles.alertSuccess}`} style={{ marginBottom: "1.25rem" }}>
          ✅ Request submitted successfully to the Regional Office!
        </div>
      )}
      {error && (
        <div className={`${styles.alert} ${styles.alertError}`} style={{ marginBottom: "1.25rem" }}>
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel} htmlFor="dept">Target RO Department</label>
          <select id="dept" name="dept" className={styles.formSelect} required>
            {activeDepts.map((d) => (
              <option key={d.Code} value={d["Name (En)"]}>{d["Name (En)"]}</option>
            ))}
            {activeDepts.length === 0 && (
              <>
                <option>OPERATIONS</option>
                <option>ADVANCES</option>
                <option>IT</option>
                <option>HRM</option>
              </>
            )}
          </select>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.formLabel} htmlFor="subject">Subject</label>
          <input id="subject" name="subject" type="text" className={styles.formInput} placeholder="Brief subject line" required />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.formLabel} htmlFor="message">Detailed Message</label>
          <textarea id="message" name="message" className={styles.formTextarea} placeholder="Describe your request or inquiry in detail…" required />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.formLabel} htmlFor="priority">Priority</label>
          <select id="priority" name="priority" className={styles.formSelect}>
            <option value="LOW">Low</option>
            <option value="NORMAL" selected>Normal</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>

        <button type="submit" className={`${styles.btnPrimary} ${styles.btnFull}`} disabled={isPending}>
          {isPending ? "Submitting…" : "📨 Submit to Regional Office"}
        </button>
      </form>
    </div>
  );
}
