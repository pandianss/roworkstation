import styles from "@/styles/components.module.css";
import type { Circular } from "@/lib/api";

interface AnnouncementCardProps {
  circular: Circular;
  animDelay?: number;
}

export default function AnnouncementCard({ circular, animDelay = 0 }: AnnouncementCardProps) {
  const ref = circular.number || circular.ref_no || circular.id || "Notice";
  const title = circular.subject || circular.title || "Regional Notice";
  const date = circular.date || (circular.created_at ? circular.created_at.substring(0, 10) : "");
  const category = circular.dept || circular.category || "General";

  return (
    <div
      className={`card ${styles.announcementCard} animate-fade-up`}
      style={{ animationDelay: `${animDelay}ms` }}
    >
      <div className={styles.announcementRef}>📄 {ref}</div>
      <div className={styles.announcementTitle}>{title}</div>
      <div className={styles.announcementMeta}>
        {date && <span>{date}</span>}
        {date && category && <span> · </span>}
        {category && (
          <span className={`badge badge--blue`}>{category}</span>
        )}
      </div>
    </div>
  );
}
