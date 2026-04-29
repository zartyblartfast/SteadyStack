"use client";

import { useState, useEffect, useRef } from "react";
import {
  Loader2,
  Zap,
  CheckCircle,
  AlertTriangle,
  Clock,
  BarChart3,
  DollarSign,
  RefreshCw,
} from "lucide-react";
import type { DecisionResponse } from "@/lib/api";
import { runDecision } from "@/lib/api";

const FEE_THRESHOLDS = {
  low: 15,
  medium: 40,
  high: 80,
};

function feeAdvice(feeRate: number | null): {
  level: "low" | "medium" | "high";
  label: string;
  description: string;
  colour: string;
  icon: typeof CheckCircle;
} {
  if (feeRate === null || feeRate <= FEE_THRESHOLDS.low) {
    return {
      level: "low",
      label: "Good Time to Buy",
      description:
        "Network fees are low. This is an efficient time to execute your DCA buy.",
      colour: "text-success",
      icon: CheckCircle,
    };
  }
  if (feeRate <= FEE_THRESHOLDS.medium) {
    return {
      level: "medium",
      label: "Fees Moderate",
      description:
        "Fees are at a normal level. You can buy now or wait a few hours for a potential dip in congestion.",
      colour: "text-warning",
      icon: Clock,
    };
  }
  return {
    level: "high",
    label: "Fees Elevated — Consider Waiting",
    description:
      "The mempool is congested and fees are high. If you can wait 12-24 hours, fees often drop during off-peak periods (weekends, early UTC mornings).",
    colour: "text-danger",
    icon: AlertTriangle,
  };
}

const PROGRESS_STAGES = [
  { label: "Checking mempool fees & congestion...", delay: 0 },
  { label: "Fetching current BTC price...", delay: 3000 },
  { label: "Analysing fee conditions...", delay: 7000 },
  { label: "Generating advisory...", delay: 12000 },
  { label: "Almost there...", delay: 20000 },
];

export default function FeeMonitorPanel() {
  const [data, setData] = useState<DecisionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressStage, setProgressStage] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

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

  async function handleCheck() {
    setLoading(true);
    setError(null);
    try {
      const result = await runDecision("balanced");
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to check fees");
    } finally {
      setLoading(false);
    }
  }

  const snap = data?.snapshot_summary;
  const feeRate = snap?.fee_rate_sat_vb ?? null;
  const advice = feeAdvice(feeRate);
  const AdviceIcon = advice.icon;

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

          {/* Market snapshot */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <div className="rounded-xl border border-card-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-accent" />
                <p className="text-xs text-muted">Fee Rate</p>
              </div>
              <p className="text-2xl font-bold tabular-nums">
                {snap.fee_rate_sat_vb ?? "N/A"}
                <span className="text-sm text-muted ml-1">sat/vB</span>
              </p>
            </div>
            <div className="rounded-xl border border-card-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-4 w-4 text-accent" />
                <p className="text-xs text-muted">BTC Price</p>
              </div>
              <p className="text-2xl font-bold tabular-nums">
                ${snap.price_usd?.toLocaleString() ?? "N/A"}
              </p>
            </div>
            <div className="rounded-xl border border-card-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-accent" />
                <p className="text-xs text-muted">Mempool</p>
              </div>
              <p className="text-2xl font-bold tabular-nums">
                {snap.mempool_depth_mb?.toFixed(1) ?? "N/A"}
                <span className="text-sm text-muted ml-1">MB</span>
              </p>
            </div>
            <div className="rounded-xl border border-card-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-4 w-4 text-accent" />
                <p className="text-xs text-muted">Est. Fee (140 vB tx)</p>
              </div>
              <p className="text-2xl font-bold tabular-nums">
                {snap.fee_rate_sat_vb && snap.price_usd
                  ? `$${((snap.fee_rate_sat_vb * 140 * snap.price_usd) / 1e8).toFixed(2)}`
                  : "N/A"}
              </p>
            </div>
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
                  <strong>Weekends &amp; early UTC mornings</strong> tend to have
                  the lowest fees — less business activity means less mempool
                  congestion.
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
