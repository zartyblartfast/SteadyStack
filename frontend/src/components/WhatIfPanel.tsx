"use client";

import { useState, useMemo, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Calculator, TrendingUp, AlertTriangle, Info, X } from "lucide-react";
import { computeProjection, SS_EDGE_BY_PROFILE } from "@/lib/projection";

const PROFILE_OPTIONS = [
  { label: "Conservative", value: "conservative", desc: "~0.5% fee savings" },
  { label: "Balanced", value: "balanced", desc: "~1% fee savings" },
  { label: "Aggressive", value: "aggressive", desc: "~1.5% fee savings" },
];

const DURATION_OPTIONS = [
  { label: "1 year", value: 1 },
  { label: "2 years", value: 2 },
  { label: "5 years", value: 5 },
  { label: "10 years", value: 10 },
  { label: "20 years", value: 20 },
];

const AMOUNT_PRESETS = [50, 100, 200, 500, 1000, 2000, 5000];

function formatUsd(v: number | undefined | null): string {
  if (v == null) return "$0";
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 100_000) return `$${(v / 1_000).toFixed(0)}k`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}k`;
  return `$${v.toFixed(0)}`;
}

function formatBtc(v: number): string {
  if (v >= 1) return `${v.toFixed(2)} BTC`;
  if (v >= 0.01) return `${v.toFixed(4)} BTC`;
  return `${Math.round(v * 1e8).toLocaleString()} sats`;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;

  // Extract values from the flat chart data shape
  const bull = data.bull as number | undefined;
  const base = data.base as number | undefined;
  const bear = data.bear as number | undefined;
  const naiveBase = data.naiveBase as number | undefined;
  const naiveBear = data.naiveBear as number | undefined;
  const naiveBull = data.naiveBull as number | undefined;
  const invested = data.invested as number | undefined;
  const year = data.year;

  return (
    <div className="rounded-lg border border-card-border bg-card px-4 py-3 text-xs shadow-lg min-w-[220px]">
      <p className="font-semibold mb-2">Year {year} — {formatUsd(invested)} invested</p>
      <div className="space-y-1.5">
        <div className="flex justify-between gap-4">
          <span className="text-success">Bull (SS)</span>
          <span>{formatUsd(bull)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-success/50">Bull (Naive)</span>
          <span className="text-muted">{formatUsd(naiveBull)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-accent">Base (SS)</span>
          <span>{formatUsd(base)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-accent/50">Base (Naive)</span>
          <span className="text-muted">{formatUsd(naiveBase)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-red-400">Bear (SS)</span>
          <span>{formatUsd(bear)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-red-400/50">Bear (Naive)</span>
          <span className="text-muted">{formatUsd(naiveBear)}</span>
        </div>
        <div className="border-t border-card-border pt-1.5 flex justify-between text-muted">
          <span>Invested</span>
          <span>{formatUsd(invested)}</span>
        </div>
      </div>
    </div>
  );
}

export default function WhatIfPanel() {
  const [monthlyAmount, setMonthlyAmount] = useState(200);
  const [duration, setDuration] = useState(10);
  const [profile, setProfile] = useState("balanced");
  const [customAmount, setCustomAmount] = useState("");
  const [mounted, setMounted] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const ssEdge = SS_EDGE_BY_PROFILE[profile] ?? 0.04;

  const { points, summary } = useMemo(
    () => computeProjection(monthlyAmount, duration, ssEdge),
    [monthlyAmount, duration, ssEdge]
  );

  // Chart data: show USD value for the area chart
  const chartData = points.map((p) => ({
    year: p.year,
    bull: Math.round(p.bullSS.usd),
    base: Math.round(p.baseSS.usd),
    bear: Math.round(p.bearSS.usd),
    naiveBase: Math.round(p.base.usd),
    naiveBear: Math.round(p.bear.usd),
    naiveBull: Math.round(p.bull.usd),
    invested: Math.round(p.totalInvested),
  }));

  const ssEdgeSats = Math.round(
    (summary.baseSS.btc - summary.base.btc) * 1e8
  );

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Calculator className="h-5 w-5 text-accent" />
            What If I DCA into Bitcoin?
          </h2>
          <p className="text-sm text-muted mt-1">Loading projections...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold flex items-center gap-2">
          <Calculator className="h-5 w-5 text-accent" />
          What If I DCA into Bitcoin?
        </h2>
        <p className="text-sm text-muted mt-1">
          See how a consistent DCA strategy could grow over time
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-6">
        {/* Amount */}
        <div className="space-y-2">
          <label className="text-xs font-medium uppercase tracking-wider text-muted">
            Monthly Amount
          </label>
          <div className="flex flex-wrap gap-2">
            {AMOUNT_PRESETS.map((amt) => (
              <button
                key={amt}
                onClick={() => { setMonthlyAmount(amt); setCustomAmount(""); }}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  monthlyAmount === amt && !customAmount
                    ? "bg-accent text-black"
                    : "border border-card-border bg-card text-foreground hover:border-accent"
                }`}
              >
                ${amt}
              </button>
            ))}
            <input
              type="number"
              placeholder="Custom"
              value={customAmount}
              onChange={(e) => {
                setCustomAmount(e.target.value);
                const v = parseInt(e.target.value);
                if (v > 0) setMonthlyAmount(v);
              }}
              className="w-24 rounded-lg border border-card-border bg-card px-3 py-1.5 text-sm text-foreground placeholder-muted focus:border-accent focus:outline-none"
            />
          </div>
        </div>

        {/* Duration */}
        <div className="space-y-2">
          <label className="text-xs font-medium uppercase tracking-wider text-muted">
            Duration
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATION_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDuration(opt.value)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  duration === opt.value
                    ? "bg-accent text-black"
                    : "border border-card-border bg-card text-foreground hover:border-accent"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Fee savings profile */}
        <div className="space-y-2">
          <label className="text-xs font-medium uppercase tracking-wider text-muted">
            Fee Savings Estimate
          </label>
          <div className="flex flex-wrap gap-2">
            {PROFILE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setProfile(opt.value)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  profile === opt.value
                    ? "bg-accent text-black"
                    : "border border-card-border bg-card text-foreground hover:border-accent"
                }`}
              >
                {opt.label}
                <span className="ml-1 text-[10px] opacity-60">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-card-border bg-card p-5">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wider text-muted">
          Projected Portfolio Value (SteadyStack-optimised)
        </h3>
        <p className="mb-4 text-xs text-muted">
          ${monthlyAmount.toLocaleString()}/mo for {duration} year{duration !== 1 ? "s" : ""} — {profile} strategy ({(ssEdge * 100).toFixed(0)}% edge)
        </p>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData} margin={{ top: 10, right: 10, bottom: 4, left: 10 }}>
            <defs>
              <linearGradient id="gradBull" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradBase" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f7931a" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f7931a" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradBear" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="year"
              type="number"
              domain={[0, duration]}
              ticks={Array.from({ length: Math.min(duration, 10) + 1 }, (_, i) =>
                duration <= 10 ? i : Math.round((i * duration) / 10)
              )}
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={{ stroke: "#1e2a3a" }}
              tickLine={false}
              tickFormatter={(v: number) => `${v}y`}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={formatUsd}
              width={55}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, color: "#64748b" }}
              iconType="square"
              iconSize={10}
            />
            <Area
              type="monotone"
              dataKey="bull"
              name="Bull"
              stroke="#22c55e"
              fill="url(#gradBull)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="base"
              name="Base"
              stroke="#f7931a"
              fill="url(#gradBase)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="bear"
              name="Bear"
              stroke="#ef4444"
              fill="url(#gradBear)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="naiveBull"
              name="Naive (Bull)"
              stroke="#22c55e"
              strokeDasharray="6 4"
              fill="none"
              strokeWidth={1.5}
              strokeOpacity={0.4}
            />
            <Area
              type="monotone"
              dataKey="naiveBase"
              name="Naive (Base)"
              stroke="#f7931a"
              strokeDasharray="6 4"
              fill="none"
              strokeWidth={1.5}
              strokeOpacity={0.4}
            />
            <Area
              type="monotone"
              dataKey="naiveBear"
              name="Naive (Bear)"
              stroke="#ef4444"
              strokeDasharray="6 4"
              fill="none"
              strokeWidth={1.5}
              strokeOpacity={0.4}
            />
            <Area
              type="monotone"
              dataKey="invested"
              name="Total Invested"
              stroke="#64748b"
              strokeDasharray="5 5"
              fill="none"
              strokeWidth={1.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Summary cards */}
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">Projected Outcomes</h3>
        <button
          onClick={() => setShowInfo(!showInfo)}
          className={`flex h-6 w-6 items-center justify-center rounded-full border transition-colors ${
            showInfo
              ? "border-accent bg-accent/10 text-accent"
              : "border-card-border text-muted hover:border-accent hover:text-accent"
          }`}
          title="Why does Bear show more BTC?"
        >
          {showInfo ? <X className="h-3 w-3" /> : <Info className="h-3 w-3" />}
        </button>
      </div>

      {showInfo && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-4 mb-4 text-sm leading-relaxed">
          <h4 className="font-semibold text-accent flex items-center gap-2 mb-2">
            <Info className="h-4 w-4" />
            Why does Bear show more BTC than Bull?
          </h4>
          <p className="text-foreground/80">
            With DCA, you buy a fixed dollar amount each month. When the price stays <strong>low</strong> (bear),
            each buy gets you <strong>more sats</strong>. When the price rises <strong>fast</strong> (bull),
            each buy gets you <strong>fewer sats</strong> — but each sat is worth much more.
          </p>
          <p className="text-foreground/80 mt-2">
            That&apos;s why the <strong>portfolio value</strong> (not the BTC amount) is the number that matters.
            In the bull case you hold fewer BTC, but they&apos;re worth significantly more.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {([
          { key: "bear" as const, label: "Bear Case", color: "text-red-400", desc: "Slow, steady growth" },
          { key: "base" as const, label: "Base Case", color: "text-accent", desc: "Historical power-law trend" },
          { key: "bull" as const, label: "Bull Case", color: "text-success", desc: "Strong adoption cycle" },
        ]).map(({ key, label, color, desc }) => {
          const ss = summary[`${key}SS` as keyof typeof summary] as { btc: number; usd: number };
          const naive = summary[key] as { btc: number; usd: number };
          const extraSats = Math.round((ss.btc - naive.btc) * 1e8);
          const roi = ((ss.usd - summary.totalInvested) / summary.totalInvested * 100).toFixed(0);
          return (
            <div key={key} className="rounded-xl border border-card-border bg-card p-4">
              <p className={`text-xs font-medium uppercase tracking-wider ${color}`}>{label}</p>
              <p className="text-[10px] text-muted mb-3">{desc}</p>
              <p className={`text-2xl font-bold tabular-nums ${color}`}>{formatUsd(ss.usd)}</p>
              <p className="text-xs text-muted mt-1">
                {formatBtc(ss.btc)} · <span className={color}>+{roi}% return</span>
              </p>
              <p className="text-xs text-muted mt-2">
                From {formatUsd(summary.totalInvested)} invested
              </p>
              <div className="mt-2 flex items-center gap-1 text-xs text-accent">
                <TrendingUp className="h-3 w-3" />
                +{extraSats.toLocaleString()} sats vs naive DCA
              </div>
            </div>
          );
        })}
      </div>

      {/* SteadyStack fee savings callout */}
      <div className="rounded-lg border border-accent/20 bg-accent/5 p-4 flex items-start gap-3">
        <TrendingUp className="h-5 w-5 text-accent mt-0.5 shrink-0" />
        <div className="text-sm">
          <p className="font-semibold text-accent">Fee Savings</p>
          <p className="text-foreground/80 mt-1">
            By monitoring mempool conditions and buying during low-fee windows, SteadyStack could save
            approximately <strong className="text-accent">{ssEdgeSats.toLocaleString()} extra sats</strong> over {duration} year{duration !== 1 ? "s" : ""} compared
            to fixed-day weekly DCA — based on ~{(ssEdge * 100).toFixed(1)}% estimated fee savings ({profile}).
            This edge grows as on-chain fees rise with each halving.
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="rounded-lg border border-warning/20 bg-warning/5 p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-warning mt-0.5 shrink-0" />
        <div className="text-xs text-muted leading-relaxed">
          <p className="font-semibold text-warning/80">Not financial advice</p>
          <p className="mt-1">
            These projections are illustrative only, based on simplified growth models loosely informed
            by historical trends. Bitcoin is volatile and past performance does not guarantee future results.
            The three scenarios represent a range of possibilities — actual outcomes may fall outside this range.
            Always do your own research and only invest what you can afford to lose.
          </p>
        </div>
      </div>
    </div>
  );
}
