"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Info,
  Loader2,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchBitcoinRisk,
  fetchBmriMetrics,
  type BitcoinRiskResponse,
  type BmriMetricsResponse,
} from "@/lib/api";

type ChartPoint = {
  date: string;
  price: number | null;
  fullIndex: number | null;
  liteIndex: number | null;
  riskScore: number | null;
  riskBand: string | null;
};

const RISK_LABELS: Record<string, string> = {
  deep_value: "deep value",
  value: "low",
  neutral: "neutral",
  elevated: "elevated",
  high: "high",
  extreme: "extreme",
};

function bmriPlainLanguage(value: number | null): string {
  if (value === null) return "BMRI context is unavailable.";
  if (value <= 5) return "Bitcoin looks deeply cheap against long-term anchors.";
  if (value <= 10) return "Bitcoin looks historically cheap right now.";
  if (value <= 35) return "Bitcoin looks below its long-term anchor range.";
  if (value <= 65) return "Bitcoin looks neutral today.";
  if (value <= 85) return "Bitcoin looks warm relative to long-term anchors.";
  return "Bitcoin looks overheated relative to long-term anchors.";
}

function riskPlainLanguage(band: string | null): string {
  if (!band) return "Bitcoin Risk context is unavailable.";
  if (band === "deep_value") return "Bitcoin Risk is in deep-value territory.";
  if (band === "value") return "Bitcoin Risk is low.";
  if (band === "neutral") return "Bitcoin Risk is neutral.";
  if (band === "elevated") return "Bitcoin Risk is elevated.";
  if (band === "high") return "Bitcoin Risk is high.";
  if (band === "extreme") return "Bitcoin Risk is extreme.";
  return `Bitcoin Risk is ${band.replaceAll("_", " ")}.`;
}

function formatUsd(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
}

function mergeHistory(bmri: BmriMetricsResponse, risk: BitcoinRiskResponse): ChartPoint[] {
  const byDate = new Map<string, ChartPoint>();

  for (const point of bmri.history) {
    byDate.set(point.date, {
      date: point.date,
      price: typeof point.price === "number" ? point.price : null,
      fullIndex: typeof point.fullIndex === "number" ? point.fullIndex : null,
      liteIndex: typeof point.liteIndex === "number" ? point.liteIndex : null,
      riskScore: null,
      riskBand: null,
    });
  }

  for (const point of risk.history) {
    const existing = byDate.get(point.date) ?? {
      date: point.date,
      price: null,
      fullIndex: null,
      liteIndex: null,
      riskScore: null,
      riskBand: null,
    };
    existing.riskScore = typeof point.riskScore === "number" ? point.riskScore : null;
    existing.riskBand = point.band ?? null;
    byDate.set(point.date, existing);
  }

  return Array.from(byDate.values())
    .sort((a, b) => a.date.localeCompare(b.date))
    .filter((point) => point.price !== null || point.fullIndex !== null || point.riskScore !== null);
}

function MetricPill({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-card-border bg-background/40 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-foreground">{value}</p>
      <p className="mt-1 text-xs text-muted">{detail}</p>
    </div>
  );
}

function PanelChart({
  data,
  title,
  dataKey,
  stroke,
  domain,
  formatter,
}: {
  data: ChartPoint[];
  title: string;
  dataKey: keyof ChartPoint;
  stroke: string;
  domain?: [number, number] | ["auto", "auto"];
  formatter?: (value: number) => string;
}) {
  return (
    <div className="rounded-xl border border-card-border bg-background/40 p-4">
      <p className="mb-3 text-sm font-medium text-foreground">{title}</p>
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 6, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="#1e2a3a" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              minTickGap={36}
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={{ stroke: "#1e2a3a" }}
              tickLine={false}
            />
            <YAxis
              domain={domain ?? ["auto", "auto"]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={58}
              tickFormatter={(value) => formatter?.(Number(value)) ?? String(value)}
            />
            <Tooltip
              contentStyle={{
                background: "#131825",
                border: "1px solid #1e2a3a",
                borderRadius: "12px",
                color: "#e2e8f0",
              }}
              labelFormatter={(label) => `Date: ${label}`}
              formatter={(value) => formatter?.(Number(value)) ?? value}
            />
            <Line
              type="monotone"
              dataKey={dataKey as string}
              stroke={stroke}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function ValuationContextPanel() {
  const [bmri, setBmri] = useState<BmriMetricsResponse | null>(null);
  const [risk, setRisk] = useState<BitcoinRiskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [bmriData, riskData] = await Promise.all([fetchBmriMetrics(), fetchBitcoinRisk()]);
      setBmri(bmriData);
      setRisk(riskData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load valuation metrics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMounted(true);
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const chartData = useMemo(() => {
    if (!bmri || !risk) return [];
    return mergeHistory(bmri, risk);
  }, [bmri, risk]);

  const latestPrice = [...chartData].reverse().find((point) => point.price !== null)?.price ?? null;
  const bmriText = bmriPlainLanguage(bmri?.full_index ?? null);
  const riskText = riskPlainLanguage(risk?.band ?? null);
  const riskBandLabel = risk?.band ? RISK_LABELS[risk.band] ?? risk.band.replaceAll("_", " ") : "—";

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-card-border bg-card p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-accent">
              <BarChart3 className="h-5 w-5" />
              <span className="text-sm font-medium uppercase tracking-wide">Valuation Context</span>
            </div>
            <h2 className="text-2xl font-bold">Price, BMRI, and Bitcoin Risk</h2>
            <p className="mt-2 max-w-3xl text-sm text-muted">
              BMRI is still the default Bear Market Boost trigger. Bitcoin Risk is shown as
              extra valuation context for now — not as a trading signal and not blended into a
              black-box score.
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-card-border px-4 py-2 text-sm text-foreground transition hover:border-accent disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="rounded-2xl border border-card-border bg-card p-8 text-center text-muted">
          <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-accent" />
          Loading valuation metrics from Bitcoin Card...
        </div>
      )}

      {error && !loading && (
        <div className="rounded-2xl border border-danger/40 bg-danger/10 p-5 text-sm text-danger">
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" />
            Valuation metrics unavailable
          </div>
          <p className="mt-2 text-danger/90">{error}</p>
        </div>
      )}

      {!loading && !error && bmri && risk && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <MetricPill label="BTC price" value={formatUsd(latestPrice)} detail="From BMRI history price points" />
            <MetricPill
              label="BMRI"
              value={`P${bmri.full_index.toFixed(1)}`}
              detail={bmriText}
            />
            <MetricPill
              label="Bitcoin Risk"
              value={`${risk.risk_score.toFixed(1)} / 100`}
              detail={`${riskText} Band: ${riskBandLabel}.`}
            />
          </div>

          <div className="rounded-2xl border border-card-border bg-card p-6">
            <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 className="text-lg font-semibold">Shared valuation chart</h3>
                <p className="mt-1 text-sm text-muted">
                  Lower BMRI and lower Bitcoin Risk generally mean cheaper/lower-risk context.
                  Price uses its own scale; BMRI and Risk use 0–100 style scales.
                </p>
              </div>
              <div className="flex items-start gap-2 rounded-xl border border-card-border bg-background/40 p-3 text-xs text-muted md:max-w-sm">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <p>
                  Sentiment, if available, is separate market context and is not part of the
                  Bitcoin Risk valuation score.
                </p>
              </div>
            </div>

            {!mounted ? (
              <div className="rounded-xl border border-card-border bg-background/40 p-8 text-center text-sm text-muted">
                Preparing valuation chart...
              </div>
            ) : chartData.length === 0 ? (
              <div className="rounded-xl border border-card-border bg-background/40 p-8 text-center text-sm text-muted">
                No valuation history available yet.
              </div>
            ) : (
              <div className="space-y-4">
                <PanelChart
                  data={chartData}
                  title="BTC price"
                  dataKey="price"
                  stroke="#f7931a"
                  formatter={formatUsd}
                />
                <PanelChart
                  data={chartData}
                  title="BMRI full index"
                  dataKey="fullIndex"
                  stroke="#22c55e"
                  domain={[0, 100]}
                  formatter={(value) => `P${value.toFixed(0)}`}
                />
                <PanelChart
                  data={chartData}
                  title="Bitcoin Risk score"
                  dataKey="riskScore"
                  stroke="#60a5fa"
                  domain={[0, 100]}
                  formatter={(value) => value.toFixed(0)}
                />
              </div>
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-card-border bg-card p-5">
              <div className="mb-2 flex items-center gap-2 text-success">
                <ShieldCheck className="h-4 w-4" />
                <h3 className="font-semibold">How SteadyStack uses this now</h3>
              </div>
              <p className="text-sm text-muted">
                Bear Market Boost still uses BMRI as the campaign trigger. Bitcoin Risk is shown
                beside it so you can see whether another valuation model agrees, disagrees, or
                adds caution.
              </p>
            </div>
            <div className="rounded-2xl border border-card-border bg-card p-5">
              <div className="mb-2 flex items-center gap-2 text-accent">
                <TrendingUp className="h-4 w-4" />
                <h3 className="font-semibold">Sources and caveats</h3>
              </div>
              <p className="text-sm text-muted">
                BMRI caveat: {bmri.source_note ?? "source caveat unavailable"}
              </p>
              <p className="mt-2 text-sm text-muted">
                Bitcoin Risk caveat: {risk.limitations ?? "risk limitations unavailable"}
              </p>
              <p className="mt-2 text-xs text-muted">
                Fetched: BMRI {bmri.fetched_at ?? "unknown"}; Risk {risk.fetched_at ?? "unknown"}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
