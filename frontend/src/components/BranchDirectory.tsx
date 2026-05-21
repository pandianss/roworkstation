"use client";

import { useState } from "react";
import styles from "@/styles/components.module.css";
import type { Unit } from "@/lib/api";

interface BranchDirectoryProps {
  units: Unit[];
}

export default function BranchDirectory({ units }: BranchDirectoryProps) {
  const [query, setQuery] = useState("");

  const active = units.filter((u) => u.Type !== "REGIONAL OFFICE");

  const filtered = query.trim()
    ? active.filter((u) => {
        const q = query.toLowerCase();
        return (
          u.Code.toLowerCase().includes(q) ||
          u.Name.toLowerCase().includes(q) ||
          (u.District ?? "").toLowerCase().includes(q)
        );
      })
    : [];

  return (
    <div>
      <div className={styles.searchWrapper}>
        <span className={styles.searchIcon}>🔍</span>
        <input
          id="branch-search"
          type="text"
          className={styles.searchInput}
          placeholder="Search by Branch Name, SOL Code, or District…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search branches by name, SOL, or district"
        />
      </div>

      {query.trim() === "" && (
        <p style={{ color: "var(--color-text-faint)", fontSize: "0.85rem", marginTop: "1rem", textAlign: "center" }}>
          Type a branch name, SOL code, or district to search
        </p>
      )}

      {query.trim() !== "" && filtered.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔍</div>
          <span>No branches match <strong>&quot;{query}&quot;</strong></span>
        </div>
      )}

      {filtered.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginTop: "1rem" }}>
          {filtered.map((u) => (
            <div key={u.Code} className={`card ${styles.branchCard} animate-fade-up`}>
              <div>
                <div className={styles.branchCode}>{u.Code}</div>
                <span className={u.Active ? styles.branchStatus : `${styles.branchStatus} ${styles.branchStatusInactive}`}>
                  {u.Active ? "Active" : "Closed"}
                </span>
              </div>
              <div>
                <div className={styles.branchName}>{u.Name}</div>
                <div className={styles.branchMeta}>
                  📍 {u.District ?? "—"} · {u["Population Group"] ?? "—"}
                  {u["Open Date"] && ` · Open: ${u["Open Date"]}`}
                </div>
                <div className={styles.branchMeta} style={{ marginTop: 4 }}>
                  👤 <strong>Head:</strong> {u.Head} &nbsp;·&nbsp;
                  👥 <strong>2nd Line:</strong> {u["2nd Line"]}
                </div>
              </div>
              <div />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
