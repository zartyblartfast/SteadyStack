"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Info,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

/* ───────────────────────── static backtest data ───────────────────────── */

const TIMING_STRATEGIES = [
  {
    name: "Policy (BUY/SKIP/WAIT)",
    edge: -33,
    desc: "Skip weeks based on price, fees, volatility signals. Buy more when conditions are favourable.",
    verdict: "Harmful — skipping weeks in a rising market means buying later at higher prices.",
  },
  {
    name: "Value Averaging (dip-weighted)",
    edge: -0.3,
    desc: "Always buy, but vary the amount based on price vs 30-day moving average.",
    verdict: "Break-even — price noise overwhelms the small dip-buying benefit.",
  },
  {
    name: "Intra-week Fee Timing",
    edge: 1.2,
    desc: "Buy on the lowest-fee day within each week instead of a fixed day.",
    verdict: "Real savings — ~1.2% fee reduction at current fee levels. Grows with every halving.",
  },
  {
    name: "Naive Weekly DCA",
    edge: 0,
    desc: "Buy the same amount every week regardless of conditions.",
    verdict: "The benchmark. Deploys capital immediately, captures the long-term uptrend.",
  },
];

const FEE_VARIATION_DATA = [
  { label: "Average weekly fee range (worst/best)", value: "2.1x" },
  { label: "Median weekly fee range", value: "1.8x" },
  { label: "Weeks with ≥2x fee range", value: "34%" },
  { label: "Weeks with ≥5x fee range", value: "3%" },
];

const HALVING_PROJECTION = [
  { year: "2024", subsidy: "3.125 BTC", feePressure: "Low", avgFee: "~$4", feeSavings: "~1%" },
  { year: "2028", subsidy: "1.5625 BTC", feePressure: "Rising", avgFee: "~$15", feeSavings: "~5%" },
  { year: "2032", subsidy: "0.78 BTC", feePressure: "High", avgFee: "~$40", feeSavings: "~13%" },
  { year: "2036+", subsidy: "~0.39 BTC", feePressure: "Dominant", avgFee: "~$100", feeSavings: "~35%" },
];

const CHART_COLOURS = {
  negative: "#ef4444",
  neutral: "#64748b",
  positive: "#22c55e",
};

/* ───────────────────────── components ───────────────────────── */

function Accordion({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-card-border bg-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-card-border/10 transition-colors"
      >
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
          {title}
        </h3>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted" />
        )}
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

/* ───────────────────────── main panel ───────────────────────── */

export default function EvidencePanel() {
  const [showMethodology, setShowMethodology] = useState(false);

  const chartData = TIMING_STRATEGIES.map((s) => ({
    name: s.name.length > 20 ? s.name.slice(0, 18) + "…" : s.name,
    fullName: s.name,
    edge: s.edge,
    fill:
      s.edge > 0.5
        ? CHART_COLOURS.positive
        : s.edge < -0.5
        ? CHART_COLOURS.negative
        : CHART_COLOURS.neutral,
  }));

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-xl border border-card-border bg-card p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold mb-2">
              Why Simple DCA Wins
            </h2>
            <p className="text-sm text-muted leading-relaxed max-w-2xl">
              We backtested 330 weeks of real Bitcoin data (Jan 2020 – Apr 2026)
              across three different &ldquo;smart&rdquo; timing strategies. The honest
              conclusion: <strong className="text-foreground">no mechanical timing strategy
              reliably beats naive weekly DCA.</strong> The one real edge is{" "}
              <strong className="text-accent">fee timing</strong> — and it
              becomes more valuable with every halving.
            </p>
          </div>
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className={`flex h-7 w-7 items-center justify-center rounded-full border shrink-0 ml-4 transition-colors ${
              showMethodology
                ? "border-accent bg-accent/10 text-accent"
                : "border-card-border text-muted hover:border-accent hover:text-accent"
            }`}
            title="Methodology"
          >
            {showMethodology ? (
              <X className="h-3.5 w-3.5" />
            ) : (
              <Info className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>

      {showMethodology && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-5 text-sm leading-relaxed space-y-3">
          <h3 className="font-semibold text-accent flex items-center gap-2">
            <Info className="h-4 w-4" />
            Methodology
          </h3>
          <ul className="space-y-2 text-foreground/80">
            <li>
              <strong>Data source:</strong> Blockchain.com Charts API — daily price,
              mempool size, transaction fees, confirmed transaction count.
            </li>
            <li>
              <strong>Period:</strong> 330 weeks (Jan 2020 – Apr 2026), covering
              COVID crash, 2021 bull, 2022 bear, 2023 recovery, 2024 ETF rally,
              and 2025 cycle.
            </li>
            <li>
              <strong>Baseline:</strong> $100 fixed weekly buy on Monday at
              market price with average daily fee rate.
            </li>
            <li>
              <strong>Fee proxy:</strong> Total daily fees USD ÷ daily confirmed
              transactions ÷ 140 vB standard tx size → estimated sat/vB.
            </li>
            <li>
              <strong>All strategies deploy the same total capital</strong> for
              fair comparison. Budget reserves are force-deployed at month end.
            </li>
          </ul>
        </div>
      )}

      {/* Strategy comparison chart */}
      <Accordion title="Timing Strategies vs Naive DCA" defaultOpen={true}>
        <div className="h-64 mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3a" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={(v: number) => `${v > 0 ? "+" : ""}${v}%`}
                stroke="#64748b"
                fontSize={12}
              />
              <YAxis
                dataKey="name"
                type="category"
                width={160}
                tick={{ fill: "#e2e8f0", fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  background: "#131825",
                  border: "1px solid #1e2a3a",
                  borderRadius: "8px",
                  fontSize: "13px",
                }}
                formatter={(value) => [
                  `${Number(value) > 0 ? "+" : ""}${value}%`,
                  "Edge vs Naive DCA",
                ]}
                labelFormatter={(_label, payload) => {
                  const item = payload?.[0]?.payload as { fullName?: string } | undefined;
                  return item?.fullName ?? "";
                }}
              />
              <Bar dataKey="edge" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Strategy details */}
        <div className="mt-4 space-y-3">
          {TIMING_STRATEGIES.map((s) => {
            const Icon =
              s.edge > 0.5
                ? TrendingUp
                : s.edge < -0.5
                ? TrendingDown
                : Minus;
            const colour =
              s.edge > 0.5
                ? "text-success"
                : s.edge < -0.5
                ? "text-danger"
                : "text-muted";

            return (
              <div
                key={s.name}
                className="flex gap-3 rounded-lg border border-card-border p-3"
              >
                <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${colour}`} />
                <div className="text-sm">
                  <p className="font-medium">
                    {s.name}
                    <span className={`ml-2 font-bold ${colour}`}>
                      {s.edge > 0 ? "+" : ""}
                      {s.edge}%
                    </span>
                  </p>
                  <p className="text-foreground/60 mt-0.5">{s.desc}</p>
                  <p className={`mt-1 text-xs font-medium ${colour}`}>
                    {s.verdict}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </Accordion>

      {/* Fee variation within weeks */}
      <Accordion title="Intra-Week Fee Variation (330 weeks)">
        <div className="grid grid-cols-2 gap-4 mt-2 lg:grid-cols-4">
          {FEE_VARIATION_DATA.map((d) => (
            <div key={d.label} className="text-center">
              <p className="text-2xl font-bold text-accent">{d.value}</p>
              <p className="text-xs text-muted mt-1">{d.label}</p>
            </div>
          ))}
        </div>
        <p className="text-sm text-foreground/70 mt-4 leading-relaxed">
          Within any given week, the cheapest day&apos;s fee rate is typically half
          the most expensive day&apos;s. By monitoring the mempool and buying on a
          low-fee day, you can save ~1–2% of your DCA investment in transaction
          costs. This doesn&apos;t sound like much, but it adds up — and it
          will matter dramatically more as on-chain fees rise.
        </p>
      </Accordion>

      {/* Halving fee projection */}
      <Accordion title="Fee Savings Growth with Halvings">
        <p className="text-sm text-foreground/70 mb-4 leading-relaxed">
          Bitcoin&apos;s block subsidy halves every ~4 years. As the subsidy
          drops, miners depend more on transaction fees for revenue, meaning
          fees must structurally increase. This makes fee-aware buying
          increasingly valuable.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-card-border text-left text-muted">
                <th className="py-2 pr-4">Halving</th>
                <th className="py-2 pr-4">Block Subsidy</th>
                <th className="py-2 pr-4">Fee Pressure</th>
                <th className="py-2 pr-4">Est. Avg Fee/tx</th>
                <th className="py-2">Fee Savings ($100 DCA)</th>
              </tr>
            </thead>
            <tbody>
              {HALVING_PROJECTION.map((row) => (
                <tr
                  key={row.year}
                  className="border-b border-card-border/50 text-foreground/80"
                >
                  <td className="py-2.5 pr-4 font-medium">{row.year}</td>
                  <td className="py-2.5 pr-4 font-mono text-xs">
                    {row.subsidy}
                  </td>
                  <td className="py-2.5 pr-4">{row.feePressure}</td>
                  <td className="py-2.5 pr-4">{row.avgFee}</td>
                  <td className="py-2.5 font-bold text-accent">
                    {row.feeSavings}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 rounded-lg border border-accent/20 bg-accent/5 p-3 flex gap-2">
          <Zap className="h-4 w-4 text-accent mt-0.5 shrink-0" />
          <p className="text-xs text-foreground/70 leading-relaxed">
            At projected 2032 fee levels, choosing the right day within the week
            to buy could save <strong className="text-accent">~13%</strong> of a
            $100 weekly DCA — the difference between accumulating 0.87 BTC and
            1.0 BTC over a year. Fee timing is not a nice-to-have; it becomes
            critical infrastructure.
          </p>
        </div>
      </Accordion>

      {/* The honest takeaway */}
      <div className="rounded-xl border border-accent/20 bg-accent/5 p-6">
        <h3 className="font-bold text-accent mb-3">The Honest Takeaway</h3>
        <ul className="space-y-2 text-sm text-foreground/80 leading-relaxed">
          <li className="flex gap-2">
            <span className="text-danger font-bold shrink-0">✗</span>
            <span>
              <strong>Price timing doesn&apos;t work.</strong> No mechanical
              strategy reliably beats naive weekly DCA on cost basis over
              multi-year periods.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-success font-bold shrink-0">✓</span>
            <span>
              <strong>Fee timing does work.</strong> Buying on the
              lowest-fee day within each week saves ~1–2% at current fee
              levels, and will save significantly more as fees rise.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-success font-bold shrink-0">✓</span>
            <span>
              <strong>Consistency is the real edge.</strong> Most people
              stop DCA during bear markets. The biggest win is simply
              keeping you accumulating through every cycle.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-success font-bold shrink-0">✓</span>
            <span>
              <strong>Sovereignty matters.</strong> Self-custody and
              node-connected workflows protect your stack and support
              Bitcoin&apos;s decentralisation.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
