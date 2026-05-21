"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment, useEffect, useState } from "react";

interface UserProfile {
  username: string;
  name: string;
  role: string;
  dept: string;
}

const NAV_ITEMS = [
  { href: "/ro",             icon: "🏠", label: "Dashboard",       section: "main" },
  { href: "/ro/mis",         icon: "📊", label: "MIS Analytics",   section: "main" },
  { href: "/ro/anniversary", icon: "🎂", label: "Anniversary",     section: "main" },
  { href: "/ro/archive",     icon: "🗄️", label: "Central Archive", section: "main" },
  { href: "/ro/campaigns",   icon: "🚀", label: "Campaigns",       section: "main" },
  { href: "/ro/performance", icon: "🏆", label: "Performance",     section: "main" },
  { href: "/ro/guardian",    icon: "🛡️", label: "Field Guardian",  section: "main" },
  { href: "/ro/visits",      icon: "🔎", label: "Branch Visits",   section: "main" },
  { href: "/ro/wizards",     icon: "🛠️", label: "Wizards",         section: "main" },
  { href: "/ro/admin",       icon: "⚙️", label: "Admin Console",   section: "admin" },
];

export default function ROLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_BASE}/api/auth/me`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setUser(data))
      .catch(() => null);
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside
        style={{
          width: 220,
          minHeight: "100vh",
          background: "hsl(220,25%,8%)",
          borderRight: "1px solid hsl(220,20%,14%)",
          display: "flex",
          flexDirection: "column",
          position: "fixed",
          top: 0,
          left: 0,
          bottom: 0,
          zIndex: 50,
          overflowY: "auto",
        }}
      >
        {/* Brand */}
        <div
          style={{
            padding: "1.25rem 1.25rem 1rem",
            borderBottom: "1px solid hsl(220,20%,14%)",
          }}
        >
          <Link
            href="/ro"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.65rem",
              textDecoration: "none",
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                background: "linear-gradient(135deg, hsl(221,83%,22%), hsl(217,91%,44%))",
                borderRadius: 8,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.1rem",
                flexShrink: 0,
              }}
            >
              🏦
            </div>
            <div>
              <div
                style={{
                  fontWeight: 800,
                  fontSize: "0.85rem",
                  color: "hsl(215,25%,94%)",
                  lineHeight: 1.2,
                }}
              >
                RO Workstation
              </div>
              <div style={{ fontSize: "0.65rem", color: "hsl(215,15%,45%)", letterSpacing: "0.06em" }}>
                DINDIGUL RO
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav style={{ padding: "0.75rem 0.6rem", flex: 1 }}>
          <div
            style={{
              fontSize: "0.6rem",
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: "hsl(215,15%,38%)",
              padding: "0.5rem 0.65rem 0.4rem",
            }}
          >
            Navigation
          </div>
          {NAV_ITEMS.map((item, idx) => {
            const isActive =
              item.href === "/ro"
                ? pathname === "/ro"
                : pathname.startsWith(item.href);
            const prevItem = NAV_ITEMS[idx - 1];
            const showDivider = item.section === "admin" && prevItem?.section !== "admin";
            return (
              <Fragment key={item.href}>
                {showDivider && (
                  <div
                    style={{
                      margin: "0.6rem 0.65rem 0.4rem",
                      borderTop: "1px solid hsl(220,20%,14%)",
                      paddingTop: "0.5rem",
                      fontSize: "0.6rem",
                      fontWeight: 700,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                      color: "hsl(215,15%,38%)",
                    }}
                  >
                    System
                  </div>
                )}
                <Link
                  href={item.href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.65rem",
                    padding: "0.55rem 0.75rem",
                    borderRadius: 8,
                    marginBottom: "0.15rem",
                    fontSize: "0.84rem",
                    fontWeight: isActive ? 600 : 500,
                    textDecoration: "none",
                    color: isActive
                      ? item.section === "admin"
                        ? "hsl(257,70%,78%)"
                        : "hsl(217,91%,72%)"
                      : "hsl(215,18%,58%)",
                    background: isActive
                      ? item.section === "admin"
                        ? "hsla(257,70%,55%,.12)"
                        : "hsla(217,91%,55%,.12)"
                      : "transparent",
                    transition: "background 120ms, color 120ms",
                  }}
                >
                  <span style={{ fontSize: "0.95rem", lineHeight: 1 }}>
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </Fragment>
            );
          })}
        </nav>

        {/* User info at bottom */}
        <div
          style={{
            padding: "0.85rem 1.1rem",
            borderTop: "1px solid hsl(220,20%,14%)",
          }}
        >
          {user ? (
            <>
              <div
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "hsl(215,25%,88%)",
                  marginBottom: "0.2rem",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {user.name}
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "0.35rem",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    fontSize: "0.62rem",
                    fontWeight: 700,
                    padding: "2px 7px",
                    borderRadius: 999,
                    background: "hsla(217,91%,55%,.15)",
                    color: "hsl(217,91%,65%)",
                    border: "1px solid hsla(217,91%,55%,.25)",
                    letterSpacing: "0.04em",
                    textTransform: "uppercase",
                  }}
                >
                  {user.role}
                </span>
                <span style={{ fontSize: "0.68rem", color: "hsl(215,15%,40%)" }}>
                  {user.dept}
                </span>
              </div>
            </>
          ) : (
            <div style={{ fontSize: "0.78rem", color: "hsl(215,15%,40%)" }}>
              Loading…
            </div>
          )}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────── */}
      <div style={{ marginLeft: 220, flex: 1, minWidth: 0 }}>
        {children}
      </div>
    </div>
  );
}
