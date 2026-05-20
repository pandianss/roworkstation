const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Unit {
  Code: string;
  Name: string;
  Type: string | null;
  District: string | null;
  "Population Group": string | null;
  Head: string;
  "2nd Line": string;
  "Effective From": string | null;
  "Open Date": string | null;
  Active: boolean;
}

export interface Department {
  Code: string;
  "Name (En)": string;
  "Name (Hi)": string;
  "Name (Ta)": string;
  Email: string;
  Active: boolean;
}

export interface MISRecord {
  DATE: string;
  SOL: number;
  "TOTAL DEPOSITS": number;
  "TOTAL ADVANCES"?: number;
  ADV: number;
  CASA?: number;
  "CD RATIO"?: number;
  "NPA %"?: number;
  "REC Q1"?: number;
  "REC Q2"?: number;
  "REC Q3"?: number;
  "REC Q4"?: number;
  "TOTAL RETAIL"?: number;
  "CORE AGRI"?: number;
  MSME?: number;
  [key: string]: unknown;
}

export interface Circular {
  id: string;
  number?: string;
  ref_no?: string;
  subject?: string;
  title?: string;
  date?: string;
  dept?: string;
  category?: string;
  created_at?: string;
}

export interface Achievement {
  id: string;
  title: string;
  desc: string;
  created_at?: string;
}

export interface Campaign {
  name: string;
  start_date: string;
  end_date: string;
  target_metric: string;
  target_value: number;
  status: string;
  branch_targets?: Record<string, number>;
}

// ── Fetch Helpers ──────────────────────────────────────────────────────────

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    next: { revalidate: 60 }, // ISR — refresh every 60 s
  });
  if (!res.ok) throw new Error(`API error ${res.status} for ${path}`);
  return res.json() as Promise<T>;
}

// ── Endpoints ──────────────────────────────────────────────────────────────

export async function getMISData(params?: {
  start_date?: string;
  end_date?: string;
}): Promise<{ data: MISRecord[] }> {
  const qs = new URLSearchParams();
  if (params?.start_date) qs.set("start_date", params.start_date);
  if (params?.end_date) qs.set("end_date", params.end_date);
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch(`/api/mis/data${query}`);
}

export async function getUnits(): Promise<{ units: Unit[] }> {
  return apiFetch("/api/master/units");
}

export async function getDepartments(): Promise<{ departments: Department[] }> {
  return apiFetch("/api/master/departments");
}

export async function getCirculars(): Promise<{ circulars: Circular[] }> {
  return apiFetch("/api/circulars");
}

export async function getAchievements(): Promise<{ achievements: Achievement[] }> {
  return apiFetch("/api/achievements");
}

export async function getCampaigns(): Promise<{ campaigns: Campaign[] }> {
  return apiFetch("/api/campaigns");
}

// ── Utility ──────────────────────────────────────────────────────────────

/** Format a number in Indian numbering system (lakhs/crores) */
export function formatIndian(value: number, decimals = 2): string {
  if (!value || isNaN(value)) return "0.00";
  const crore = value / 100; // backend stores in lakhs
  return crore.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Format a raw backend value (in lakhs) as "₹ X.XX Cr" */
export function formatCrore(val: number): string {
  return `₹ ${formatIndian(val)} Cr`;
}
