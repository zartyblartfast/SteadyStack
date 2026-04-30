"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  Loader2,
  Zap,
  CheckCircle,
  AlertTriangle,
  Clock,
  BarChart3,
  DollarSign,
  RefreshCw,
  Info,
  TrendingDown,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type { DecisionResponse, FeeHistoryEntry, FeeHistoryPeriod } from "@/lib/api";
import { runDecision, fetchFeeHistory } from "@/lib/api";

/* ───────── constants ───────── */

const DEFAULT_BUY_THRESHOLD = 5;
const DEFAULT_WAIT_THRESHOLD = 15;

const PERIOD_OPTIONS: { value: FeeHistoryPeriod; label: string }[] = [
  { value: "24h", label: "24h" },
  { value: "3d", label: "3D" },
  { value: "1w", label: "1W" },
  { value: "1m", label: "1M" },
  { value: "3m", label: "3M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "2y", label: "2Y" },
  { value: "3y", label: "3Y" },
];

function feeAdvice(
  feeRate: number | null,
  buyThreshold: number,
  waitThreshold: number
): {
  level: "low" | "medium" | "high";
  label: string;
  description: string;
  colour: string;
  icon: typeof CheckCircle;
} {
  if (feeRate === null || feeRate <= buyThreshold) {
    return {
      level: "low",
      label: "Fees Below Target",
      description:
        `Current fees${feeRate !== null ? ` (${feeRate} sats/vB)` : ""} are at or below your target of ${buyThreshold} sats/vB. This is an efficient time to execute your DCA buy.`,
      colour: "text-success",
      icon: CheckCircle,
    };
  }
  if (feeRate <= waitThreshold) {
    return {
      level: "medium",
      label: "Fees Above Target",
      description:
        `Current fees (${feeRate} sats/vB) are above your target of ${buyThreshold} sats/vB. You could buy now or wait a few hours for a potential dip.`,
      colour: "text-warning",
      icon: Clock,
    };
  }
  return {
    level: "high",
    label: "Fees Well Above Target",
    description:
      `Current fees (${feeRate} sats/vB) are significantly above your target of ${buyThreshold} sats/vB. Consider waiting — fees often drop during off-peak periods (weekends and ${localLowFeeWindow()}).`,
    colour: "text-danger",
    icon: AlertTriangle,
  };
}

function feeToUsd(satPerVb: number, priceUsd: number, txSize: number = 140): string {
  return ((satPerVb * txSize * priceUsd) / 1e8).toFixed(2);
}

function formatTimestamp(ts: number, period: FeeHistoryPeriod): string {
  const d = new Date(ts * 1000);
  if (period === "24h" || period === "3d") {
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }
  if (period === "1y" || period === "2y" || period === "3y") {
    return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  }
  if (period === "3m" || period === "6m") {
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function localLowFeeWindow(): string {
  const fmt = (h: number) => {
    const d = new Date();
    d.setUTCHours(h, 0, 0, 0);
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  };
  return `${fmt(2)}–${fmt(8)} local time`;
}

const PROGRESS_STAGES = [
  { label: "Checking mempool fees & congestion...", delay: 0 },
  { label: "Fetching current BTC price...", delay: 3000 },
  { label: "Analysing fee conditions...", delay: 7000 },
  { label: "Generating advisory...", delay: 12000 },
  { label: "Almost there...", delay: 20000 },
];

/* ───────── stat card helper ───────── */

function StatCard({
  icon: Icon,
  label,
  value,
  unit,
  tooltip,
}: {
  icon: typeof Zap;
  label: string;
  value: string;
  unit?: string;
  tooltip?: string;
}) {
  return (
    <div className="rounded-xl border border-card-border bg-card p-4 relative group">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4 text-accent" />
        <p className="text-xs text-muted">{label}</p>
        {tooltip && (
          <div className="relative">
            <Info className="h-3 w-3 text-muted/50 cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-52 rounded-lg bg-[#131825] border border-card-border p-2 text-xs text-foreground/80 z-50 shadow-lg">
              {tooltip}
            </div>
          </div>
        )}
      </div>
      <p className="text-2xl font-bold tabular-nums">
        {value}
        {unit && <span className="text-sm text-muted ml-1">{unit}</span>}
      </p>
    </div>
  );
}

/* ───────── main component ───────── */

export default function FeeMonitorPanel() {
  const [data, setData] = useState<DecisionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressStage, setProgressStage] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const [feeHistory, setFeeHistory] = useState<FeeHistoryEntry[]>([]);
  const [historyPeriod, setHistoryPeriod] = useState<FeeHistoryPeriod>("1w");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [buyThreshold, setBuyThreshold] = useState(DEFAULT_BUY_THRESHOLD);
  const waitThreshold = buyThreshold * 3;

  useEffect(() => {
    if (loading) {
      setProgressStage(0);
      timersRef.current = PROGRESS_STAGES.slice(1).map((stage, i) =>
        setTimeout(() => setProgressStage(i + 1), stage.delay)
      );
    } else {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
    }
    return () => {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
    };
  }, [loading]);

  const loadHistory = useCallback(async (period: FeeHistoryPeriod) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const entries = await fetchFeeHistory(period);
      setFeeHistory(entries);
    } catch (e) {
      setHistoryError(e instanceof Error ? e.message : "Failed to load fee history");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  async function handleCheck() {
    setLoading(true);
    setError(null);
    try {
      const result = await runDecision("balanced");
      setData(result);
      // Also load fee history on first check
      if (feeHistory.length === 0) {
        loadHistory(historyPeriod);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to check fees");
    } finally {
      setLoading(false);
    }
  }

  function handlePeriodChange(period: FeeHistoryPeriod) {
    setHistoryPeriod(period);
    loadHistory(period);
  }

  const snap = data?.snapshot_summary;
  const feeRate = snap?.fee_rate_sat_vb ?? null;
  const advice = feeAdvice(feeRate, buyThreshold, waitThreshold);
  const AdviceIcon = advice.icon;

  // Prepare chart data
  // Floor at 1 sat/vB — the network minimum relay fee.
  // Zeros are artefacts from miners including their own 0-fee transactions.
  const floor1 = (v: number) => Math.max(v, 1);
  const chartData = feeHistory.map((entry) => ({
    time: entry.timestamp,
    label: formatTimestamp(entry.timestamp, historyPeriod),
    median: floor1(entry.avgFee_50),
    low: floor1(entry.avgFee_10),
    high: floor1(entry.avgFee_90),
  }));

  // Ensure Y axis always shows up to at least the buy zone threshold
  const dataMax = chartData.length > 0
    ? Math.max(...chartData.map((d) => d.high || d.median || 0))
    : 0;
  const yAxisMax = Math.ceil(Math.max(dataMax * 1.1, buyThreshold * 1.5));

  // Compute average and standard deviation from fee history
  const medianFees = chartData.map((d) => d.median).filter((v) => v != null && v > 0);
  const feeAvg = medianFees.length > 0
    ? medianFees.reduce((a, b) => a + b, 0) / medianFees.length
    : null;
  const feeStdDev = feeAvg !== null && medianFees.length > 1
    ? Math.sqrt(medianFees.reduce((sum, v) => sum + (v - feeAvg) ** 2, 0) / medianFees.length)
    : null;

  return (
    <div className="space-y-6">
      {/* Intro */}
      <div className="rounded-xl border border-card-border bg-card p-6">
        <h2 className="text-lg font-bold mb-2">Fee Monitor</h2>
        <p className="text-sm text-muted leading-relaxed">
          Bitcoin transaction fees vary significantly throughout the day and week.
          Check current conditions before executing your DCA buy to avoid overpaying.
          As block subsidies decrease with each halving, fee savings become
          increasingly valuable.
        </p>
        <button
          onClick={handleCheck}
          disabled={loading}
          className="mt-4 flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-black transition-colors hover:bg-accent-dim disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {loading ? "Checking..." : "Check Current Fees"}
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-3 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3">
          <Loader2 className="h-4 w-4 animate-spin text-accent shrink-0" />
          <div>
            <p className="text-sm font-medium text-accent">
              {PROGRESS_STAGES[progressStage].label}
            </p>
            <p className="text-xs text-muted mt-0.5">
              This typically takes 10–30 seconds
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
          {error}
        </div>
      )}

      {data && snap && (
        <>
          {/* Fee advisory */}
          <div
            className={`rounded-xl border p-6 ${
              advice.level === "low"
                ? "border-success/30 bg-success/5"
                : advice.level === "medium"
                ? "border-warning/30 bg-warning/5"
                : "border-danger/30 bg-danger/5"
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-full ${
                  advice.level === "low"
                    ? "bg-success/10"
                    : advice.level === "medium"
                    ? "bg-warning/10"
                    : "bg-danger/10"
                }`}
              >
                <AdviceIcon className={`h-6 w-6 ${advice.colour}`} />
              </div>
              <div>
                <p className={`text-xl font-bold ${advice.colour}`}>
                  {advice.label}
                </p>
                <p className="text-sm text-foreground/80 mt-1">
                  {advice.description}
                </p>
              </div>
            </div>
          </div>

          {/* Fee tiers */}
          <div className="rounded-xl border border-card-border bg-card p-5">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">
              Current Fee Rates
            </h3>
            <p className="text-xs text-muted mb-4">
              Fees are measured in <strong>sats/vB</strong> (satoshis per virtual byte) — the price you
              pay per unit of transaction data. A typical DCA buy transaction is ~140 vB.
            </p>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <div className="rounded-lg bg-[#0d1117] p-3 border border-card-border">
                <p className="text-xs text-muted mb-1">⚡ Next Block</p>
                <p className="text-lg font-bold tabular-nums">
                  {snap.fastest_fee ?? "N/A"} <span className="text-xs text-muted">sats/vB</span>
                </p>
                {snap.fastest_fee && snap.price_usd && (
                  <p className="text-xs text-muted mt-0.5">
                    ≈ ${feeToUsd(snap.fastest_fee, snap.price_usd)} per tx
                  </p>
                )}
              </div>
              <div className="rounded-lg bg-[#0d1117] p-3 border border-card-border">
                <p className="text-xs text-muted mb-1">🕐 ~30 min</p>
                <p className="text-lg font-bold tabular-nums">
                  {snap.half_hour_fee ?? "N/A"} <span className="text-xs text-muted">sats/vB</span>
                </p>
                {snap.half_hour_fee && snap.price_usd && (
                  <p className="text-xs text-muted mt-0.5">
                    ≈ ${feeToUsd(snap.half_hour_fee, snap.price_usd)} per tx
                  </p>
                )}
              </div>
              <div className={`rounded-lg p-3 border ${
                feeRate !== null && feeRate <= buyThreshold
                  ? "bg-success/5 border-success/30"
                  : "bg-[#0d1117] border-card-border"
              }`}>
                <p className="text-xs text-muted mb-1">⏳ ~1 hour</p>
                <p className="text-lg font-bold tabular-nums">
                  {snap.hour_fee ?? "N/A"} <span className="text-xs text-muted">sats/vB</span>
                </p>
                {snap.hour_fee && snap.price_usd && (
                  <p className="text-xs text-muted mt-0.5">
                    ≈ ${feeToUsd(snap.hour_fee, snap.price_usd)} per tx
                  </p>
                )}
                <p className="text-[10px] text-accent mt-1">← Used for DCA advisory</p>
              </div>
              <div className="rounded-lg bg-[#0d1117] p-3 border border-card-border">
                <p className="text-xs text-muted mb-1">🐢 Economy</p>
                <p className="text-lg font-bold tabular-nums">
                  {snap.economy_fee ?? "N/A"} <span className="text-xs text-muted">sats/vB</span>
                </p>
                {snap.economy_fee && snap.price_usd && (
                  <p className="text-xs text-muted mt-0.5">
                    ≈ ${feeToUsd(snap.economy_fee, snap.price_usd)} per tx
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Market snapshot */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <StatCard
              icon={DollarSign}
              label="BTC Price"
              value={`$${snap.price_usd?.toLocaleString() ?? "N/A"}`}
            />
            <StatCard
              icon={BarChart3}
              label="Mempool Size"
              value={snap.mempool_depth_mb?.toFixed(1) ?? "N/A"}
              unit="MB"
              tooltip="Total size of unconfirmed transactions waiting to be mined. Larger mempool = higher fees."
            />
            <StatCard
              icon={TrendingDown}
              label="Est. Buy Cost"
              value={
                snap.hour_fee && snap.price_usd
                  ? `$${feeToUsd(snap.hour_fee, snap.price_usd)}`
                  : "N/A"
              }
              tooltip="Estimated on-chain transaction fee for a typical DCA buy (~140 virtual bytes) at the current 1-hour fee rate."
            />
            <StatCard
              icon={BarChart3}
              label={`Avg Fee (${historyPeriod})`}
              value={feeAvg !== null ? feeAvg.toFixed(1) : "N/A"}
              unit="sats/vB"
              tooltip={`Average median fee rate over the selected ${historyPeriod} period. Helps gauge the typical fee level.`}
            />
            <StatCard
              icon={BarChart3}
              label={`Std Dev (${historyPeriod})`}
              value={feeStdDev !== null ? feeStdDev.toFixed(1) : "N/A"}
              unit="sats/vB"
              tooltip={`Standard deviation of median fees over the ${historyPeriod} period. Lower = more stable fees; higher = more volatility.`}
            />
          </div>

          {/* Historical fee chart */}
          <div className="rounded-xl border border-card-border bg-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
                Fee History
              </h3>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-muted whitespace-nowrap">Buy zone ≤</label>
                  <input
                    type="range"
                    min={1}
                    max={20}
                    step={1}
                    value={buyThreshold}
                    onChange={(e) => setBuyThreshold(Number(e.target.value))}
                    className="w-40 h-1.5 accent-[#22c55e] cursor-pointer"
                  />
                  <span className="text-xs font-semibold text-[#22c55e] tabular-nums w-14">{buyThreshold} sats/vB</span>
                </div>
                <div className="flex gap-1">
                  {PERIOD_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handlePeriodChange(opt.value)}
                      disabled={historyLoading}
                      className={`px-3 py-1 text-xs rounded-md transition-colors ${
                        historyPeriod === opt.value
                          ? "bg-accent text-black font-semibold"
                          : "text-muted hover:text-foreground hover:bg-card-border/30"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {historyLoading && (
              <div className="flex items-center gap-2 py-8 justify-center">
                <Loader2 className="h-4 w-4 animate-spin text-accent" />
                <span className="text-sm text-muted">Loading fee data...</span>
              </div>
            )}

            {historyError && (
              <p className="text-sm text-danger py-4">{historyError}</p>
            )}

            {!historyLoading && chartData.length > 0 && (
              <>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <defs>
                        <linearGradient id="feeGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                          <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
                        </linearGradient>
                        <linearGradient id="rangeGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#94a3b8" stopOpacity={0.35} />
                          <stop offset="100%" stopColor="#94a3b8" stopOpacity={0.08} />
                        </linearGradient>
                      </defs>
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#64748b", fontSize: 10 }}
                        stroke="#1e2a3a"
                        interval="preserveStartEnd"
                        minTickGap={80}
                      />
                      <YAxis
                        tick={{ fill: "#64748b", fontSize: 10 }}
                        stroke="#1e2a3a"
                        tickFormatter={(v: number) => `${Math.round(v)}`}
                        width={40}
                        domain={[0, yAxisMax]}
                        allowDecimals={false}
                        label={{ value: "sats/vB", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 10, offset: 10 }}
                      />
                      <RechartsTooltip
                        contentStyle={{
                          background: "#131825",
                          border: "1px solid #1e2a3a",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                        labelStyle={{ color: "#94a3b8" }}
                        itemStyle={{ color: "#e2e8f0" }}
                        formatter={(value, name) => {
                          const labels: Record<string, string> = {
                            median: "Median fee",
                            high: "90th percentile",
                            low: "10th percentile",
                          };
                          return [`${value} sats/vB`, labels[String(name)] ?? name];
                        }}
                      />
                      {/* Buy zone: below the low threshold */}
                      <ReferenceArea
                        y1={0}
                        y2={buyThreshold}
                        fill="#22c55e"
                        fillOpacity={0.18}
                        label={{ value: `Buy zone (≤${buyThreshold})`, position: "insideTopLeft", fill: "#22c55e", fontSize: 10, fontWeight: 600 }}
                      />
                      <ReferenceLine
                        y={buyThreshold}
                        stroke="#22c55e"
                        strokeDasharray="6 3"
                        strokeWidth={1.5}
                      />
                      {waitThreshold <= yAxisMax && (
                        <ReferenceLine
                          y={waitThreshold}
                          stroke="#f59e0b"
                          strokeDasharray="4 4"
                          strokeWidth={1}
                          label={{ value: `Wait (>${waitThreshold})`, position: "insideTopLeft", fill: "#f59e0b", fontSize: 10 }}
                        />
                      )}
                      <Area
                        type="monotone"
                        dataKey="high"
                        stroke="transparent"
                        fill="url(#rangeGrad)"
                        isAnimationActive={false}
                      />
                      <Area
                        type="monotone"
                        dataKey="median"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="url(#feeGrad)"
                        isAnimationActive={false}
                      />
                      <Area
                        type="monotone"
                        dataKey="low"
                        stroke="#94a3b8"
                        strokeWidth={1}
                        strokeDasharray="3 3"
                        fill="transparent"
                        isAnimationActive={false}
                      />
                      {/* Current fee as a horizontal marker */}
                      {feeRate !== null && (
                        <ReferenceLine
                          y={feeRate}
                          stroke="#3b82f6"
                          strokeWidth={2}
                          label={{ value: `Now: ${feeRate} sats/vB`, position: "right", fill: "#3b82f6", fontSize: 10, fontWeight: 600 }}
                        />
                      )}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex items-center gap-4 mt-2 text-[10px] text-muted">
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-0.5 bg-[#f59e0b]" /> Median fee
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-0.5 bg-[#64748b]" style={{ borderTop: "1px dashed #64748b" }} /> 10th–90th percentile
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-0.5 bg-[#3b82f6]" /> Current rate
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-2 bg-[#22c55e]/20 border border-[#22c55e]/40 rounded-sm" /> Buy zone (≤{buyThreshold} sats/vB)
                  </span>
                </div>
              </>
            )}

            {!historyLoading && chartData.length === 0 && !historyError && (
              <p className="text-sm text-muted py-4 text-center">
                Click &ldquo;Check Current Fees&rdquo; to load historical fee data.
              </p>
            )}
          </div>

          {/* Fee tips */}
          <div className="rounded-xl border border-card-border bg-card p-5">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">
              Fee Timing Tips
            </h3>
            <ul className="space-y-3 text-sm text-foreground/80">
              <li className="flex gap-2">
                <Zap className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                <span>
                  <strong>Weekends &amp; off-peak hours</strong> tend to have
                  the lowest fees. The quietest window is typically 02:00–08:00
                  UTC ({localLowFeeWindow()}) when US and European markets are
                  closed.
                </span>
              </li>
              <li className="flex gap-2">
                <Zap className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                <span>
                  <strong>Fees vary ~2x within a typical week.</strong> Our
                  backtesting over 330 weeks found that 34% of weeks had a 2x+
                  fee range between the cheapest and most expensive day.
                </span>
              </li>
              <li className="flex gap-2">
                <Zap className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                <span>
                  <strong>Don&apos;t delay your DCA for price.</strong> Waiting
                  for a &ldquo;better price&rdquo; doesn&apos;t work —
                  backtesting confirms no timing strategy reliably beats weekly
                  DCA. Only delay for fees.
                </span>
              </li>
              <li className="flex gap-2">
                <Zap className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                <span>
                  <strong>Fee savings compound with halvings.</strong> As the
                  block subsidy drops (3.125 → 1.5625 → 0.78 BTC), miners
                  depend more on fees. This fee monitor becomes more valuable
                  every cycle.
                </span>
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
