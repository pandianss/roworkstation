import Link from "next/link";
import styles from "@/styles/components.module.css";

interface NavBarProps {
  activePage?: "guest" | "branch";
  sol?: string;
}

export default function NavBar({ activePage, sol }: NavBarProps) {
  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.navbarBrand}>
        <div className={styles.navLogo}>🏦</div>
        <span>RO Workstation</span>
      </Link>

      <div className={styles.navLinks}>
        <Link
          href="/"
          className={`${styles.navLink} ${activePage === "guest" ? styles.navLinkActive : ""}`}
        >
          Regional Portal
        </Link>
        {sol && (
          <Link
            href={`/branch/${sol}`}
            className={`${styles.navLink} ${activePage === "branch" ? styles.navLinkActive : ""}`}
          >
            Branch {sol}
          </Link>
        )}
        <span className={`badge badge--blue`} style={{ marginLeft: "0.5rem" }}>
          Live Data
        </span>
      </div>
    </nav>
  );
}
