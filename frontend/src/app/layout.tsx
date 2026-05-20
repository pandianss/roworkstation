import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RO Workstation | Regional Office Banking Portal",
  description:
    "Dindigul Regional Office — Transparency and Excellence in Banking. Regional business performance, branch directory, and organizational overview.",
  keywords: "regional office banking, MIS analytics, branch performance, Dindigul, Indian bank regional portal",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
