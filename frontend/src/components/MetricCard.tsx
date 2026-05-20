import styles from "@/styles/components.module.css";

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: "blue" | "green" | "amber";
  animDelay?: number;
}

export default function MetricCard({ label, value, sub, accent = "blue", animDelay = 0 }: MetricCardProps) {
  const accentClass =
    accent === "green" ? styles.metricAccent :
    accent === "amber" ? styles.metricAmber :
    "";

  return (
    <div
      className={`card ${styles.metricCard} animate-fade-up`}
      style={{ animationDelay: `${animDelay}ms` }}
    >
      <span className={styles.metricLabel}>{label}</span>
      <span className={`${styles.metricValue} ${accentClass}`}>{value}</span>
      {sub && <span className={styles.metricSub}>{sub}</span>}
    </div>
  );
}
