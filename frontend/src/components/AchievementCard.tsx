import styles from "@/styles/components.module.css";
import type { Achievement } from "@/lib/api";

const ICONS = ["🌟", "🏆", "🎯", "💡", "⭐", "🚀", "🎖️"];

interface AchievementCardProps {
  achievement: Achievement;
  index?: number;
  animDelay?: number;
}

export default function AchievementCard({ achievement, index = 0, animDelay = 0 }: AchievementCardProps) {
  return (
    <div
      className={`card ${styles.achievementCard} animate-fade-up`}
      style={{ animationDelay: `${animDelay}ms` }}
    >
      <div className={styles.achievementIcon}>{ICONS[index % ICONS.length]}</div>
      <div className={styles.achievementTitle}>{achievement.title}</div>
      <div className={styles.achievementDesc}>{achievement.desc}</div>
    </div>
  );
}
