import Link from "next/link";
import styles from "@/styles/components.module.css";
import type { UserProfile } from "@/lib/api";

interface NavBarProps {
  activePage?: "guest" | "ro" | "branch";
  sol?: string;
  user?: UserProfile;
}

export default function NavBar({ activePage, sol, user }: NavBarProps) {
  const roleLabel = user?.role === "ADMIN" ? "RO Staff" : user?.role === "USER" ? "Branch Staff" : "Guest";
  const roleBadgeClass = user?.role === "ADMIN" ? "badge--green" : user?.role === "USER" ? "badge--blue" : "";

  return (
    <nav className={styles.navbar}>
      <Link href={user?.portal === "ro" ? "/ro" : user?.portal === "branch" && sol ? `/branch/${sol}` : "/"} className={styles.navbarBrand}>
        <div className={styles.navLogo}>🏦</div>
        <span>RO Workstation</span>
      </Link>

      <div className={styles.navLinks}>
        {/* RO Portal link — only visible to ADMIN users */}
        {user?.role === "ADMIN" && (
          <Link
            href="/ro"
            className={`${styles.navLink} ${activePage === "ro" ? styles.navLinkActive : ""}`}
          >
            Regional Portal
          </Link>
        )}

        {/* Branch Portal link */}
        {sol && (
          <Link
            href={`/branch/${sol}`}
            className={`${styles.navLink} ${activePage === "branch" ? styles.navLinkActive : ""}`}
          >
            Branch {sol}
          </Link>
        )}

        {/* Guest Portal link — always visible */}
        <Link
          href="/"
          className={`${styles.navLink} ${activePage === "guest" ? styles.navLinkActive : ""}`}
        >
          Public Portal
        </Link>

        {/* Live data badge */}
        <span className="badge badge--blue" style={{ marginLeft: "0.25rem" }}>
          Live Data
        </span>

        {/* User identity badge */}
        {user && user.role !== "GUEST" && (
          <span className={`badge ${roleBadgeClass}`} style={{ marginLeft: "0.25rem" }}>
            {user.name} · {roleLabel}
          </span>
        )}
      </div>
    </nav>
  );
}
