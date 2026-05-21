"use client";

import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Area, AreaChart,
} from "recharts";

interface ChartData {
  [key: string]: string | number;
}

type ChartKind = "pie" | "bar" | "line" | "area";

interface SectionChartProps {
  data: ChartData[];
  xKey: string;
  yKeys: string | string[];
  title?: string;
  kind?: ChartKind;
  height?: number;
}

const COLORS = [
  "hsl(217,91%,55%)",
  "hsl(158,76%,45%)",
  "hsl(38,95%,55%)",
  "hsl(257,70%,65%)",
  "hsl(0,84%,60%)",
];

const TOOLTIP_STYLE = {
  backgroundColor: "hsl(222,40%,12%)",
  border: "1px solid hsl(222,30%,22%)",
  borderRadius: 8,
  color: "hsl(215,25%,94%)",
  fontSize: "0.8rem",
};

function formatVal(v: number): string {
  if (v >= 100) return `${(v / 100).toFixed(2)} Cr`;
  return v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

export default function SectionChart({
  data, xKey, yKeys, title, kind = "bar", height = 280,
}: SectionChartProps) {
  const keys = Array.isArray(yKeys) ? yKeys : [yKeys];

  if (!data || data.length === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: height, color: "var(--color-text-faint)", fontSize: "0.85rem" }}>
        No data available
      </div>
    );
  }

  const axisStyle = { fontSize: "0.7rem", fill: "hsl(215,18%,50%)" };

  if (kind === "pie") {
    return (
      <div>
        {title && <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--color-text-muted)", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>{title}</h4>}
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              dataKey={keys[0]}
              nameKey={xKey}
              cx="50%" cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={3}
              strokeWidth={0}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(v: unknown) => [formatVal(Number(v ?? 0)), ""]}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              formatter={(v) => <span style={{ fontSize: "0.75rem", color: "hsl(215,18%,60%)" }}>{v}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (kind === "area") {
    return (
      <div>
        {title && <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--color-text-muted)", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>{title}</h4>}
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              {keys.map((k, i) => (
                <linearGradient key={k} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS[i]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS[i]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/100).toFixed(0)}`} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: unknown) => [formatVal(Number(v ?? 0)), ""]} />
            <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ fontSize: "0.75rem", color: "hsl(215,18%,60%)" }}>{v}</span>} />
            {keys.map((k, i) => (
              <Area key={k} type="monotone" dataKey={k} stroke={COLORS[i]} strokeWidth={2} fill={`url(#grad-${i})`} dot={false} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Bar chart (default)
  return (
    <div>
      {title && <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--color-text-muted)", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>{title}</h4>}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
          <YAxis tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/100).toFixed(0)}`} />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: unknown) => [formatVal(Number(v ?? 0)), ""]} />
          <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ fontSize: "0.75rem", color: "hsl(215,18%,60%)" }}>{v}</span>} />
          {keys.map((k, i) => (
            <Bar key={k} dataKey={k} fill={COLORS[i]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
