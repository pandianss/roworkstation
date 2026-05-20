import styles from "@/styles/components.module.css";
import type { Unit } from "@/lib/api";

interface DemographicsPanelProps {
  units: Unit[];
}

function ProgressBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className={styles.progressTrack}>
      <div className={styles.progressFill} style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export default function DemographicsPanel({ units }: DemographicsPanelProps) {
  const active = units.filter((u) => u.Type !== "REGIONAL OFFICE" && u.Active);

  const popGroups = active.map((u) => (u["Population Group"] ?? "").toUpperCase().trim());
  const total = active.length || 1;

  const ruralCount     = popGroups.filter((g) => g === "RURAL").length;
  const semiUrbanCount = popGroups.filter((g) => g === "SEMI URBAN").length;
  const urbanCount     = popGroups.filter((g) => g === "URBAN").length;

  const ruralPct     = Math.round((ruralCount / total) * 100);
  const semiUrbanPct = Math.round((semiUrbanCount / total) * 100);
  const urbanPct     = Math.round((urbanCount / total) * 100);

  // District distribution
  const districtMap: Record<string, number> = {};
  active.forEach((u) => {
    const d = (u.District ?? "Unknown").trim();
    districtMap[d] = (districtMap[d] ?? 0) + 1;
  });
  const districts = Object.entries(districtMap).sort((a, b) => b[1] - a[1]);
  const maxDist = Math.max(...districts.map((d) => d[1]), 1);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
      {/* Population Sectors */}
      <div className={`card ${styles.demoPanel}`}>
        <div className={styles.demoPanelTitle} style={{ color: "hsl(217,91%,65%)" }}>
          🌾 Population Sectors
        </div>
        <div className={styles.demoRow}>
          {[
            { label: "🏡 Semi-Urban", count: semiUrbanCount, pct: semiUrbanPct, color: "hsl(217,91%,55%)" },
            { label: "🌾 Rural",      count: ruralCount,     pct: ruralPct,     color: "hsl(158,76%,45%)" },
            { label: "🏢 Urban",      count: urbanCount,     pct: urbanPct,     color: "hsl(38,95%,55%)" },
          ].map(({ label, count, pct, color }) => (
            <div key={label} className={styles.demoItem}>
              <div className={styles.demoItemMeta}>
                <span className={styles.demoItemLabel}>{label}</span>
                <span className={styles.demoItemValue}>{count} ({pct}%)</span>
              </div>
              <ProgressBar pct={pct} color={color} />
            </div>
          ))}
        </div>
      </div>

      {/* District Coverage */}
      <div className={`card ${styles.demoPanel}`}>
        <div className={styles.demoPanelTitle} style={{ color: "hsl(257,70%,70%)" }}>
          📍 District Coverage
        </div>
        <div className={styles.demoRow}>
          {districts.slice(0, 5).map(([dist, count]) => {
            const pct = Math.round((count / maxDist) * 100);
            return (
              <div key={dist} className={styles.demoItem}>
                <div className={styles.demoItemMeta}>
                  <span className={styles.demoItemLabel}>{dist}</span>
                  <span className={styles.demoItemValue}>{count} branches</span>
                </div>
                <ProgressBar pct={pct} color="hsl(257,70%,60%)" />
              </div>
            );
          })}
        </div>
      </div>

      {/* Network Stats */}
      <div className={`card ${styles.demoPanel}`}>
        <div className={styles.demoPanelTitle} style={{ color: "hsl(158,76%,50%)" }}>
          📊 Network Overview
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {[
            { label: "Total Active Branches", value: `${active.length}`, icon: "🏦" },
            { label: "Districts Covered",     value: `${districts.length}`,    icon: "📍" },
            { label: "Rural Outreach",        value: `${ruralPct}%`,           icon: "🌾" },
          ].map(({ label, value, icon }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <div style={{ fontSize: "1.5rem", width: 36, textAlign: "center" }}>{icon}</div>
              <div>
                <div style={{ fontWeight: 800, fontSize: "1.3rem", color: "var(--color-text)", lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: "0.78rem", color: "var(--color-text-muted)", marginTop: 2 }}>{label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
