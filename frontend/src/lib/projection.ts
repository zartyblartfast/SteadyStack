/**
 * DCA projection model.
 *
 * Computes accumulated BTC and estimated USD value over time for
 * three growth scenarios (bear, base, bull).
 *
 * Growth rates are annualised compound rates that taper over long
 * horizons, loosely informed by Bitcoin's historical power-law trend.
 *
 * SteadyStack edge is modelled as a modest fee-savings improvement
 * (~0.5-1.5% fee savings, backed by 330-week backtest — see ADR-015).
 *
 * All computation is client-side — no API calls needed.
 */

export interface ProjectionPoint {
  month: number;
  year: number;
  totalInvested: number;
  bear: { btc: number; usd: number };
  base: { btc: number; usd: number };
  bull: { btc: number; usd: number };
  bearSS: { btc: number; usd: number };
  baseSS: { btc: number; usd: number };
  bullSS: { btc: number; usd: number };
}

export interface ProjectionSummary {
  totalInvested: number;
  bear: { btc: number; usd: number };
  base: { btc: number; usd: number };
  bull: { btc: number; usd: number };
  bearSS: { btc: number; usd: number };
  baseSS: { btc: number; usd: number };
  bullSS: { btc: number; usd: number };
}

// Starting BTC price anchor (approximate current price)
const BTC_START_PRICE = 76000;

// Annualised growth rates (CAGR) for each scenario.
// These taper for projections beyond 5 years to stay conservative.
function annualGrowthRate(
  scenario: "bear" | "base" | "bull",
  yearsIn: number
): number {
  const rates = {
    bear: { early: 0.05, late: 0.03 },   // ~5% early, ~3% late
    base: { early: 0.28, late: 0.15 },   // ~28% early, ~15% late (power-law)
    bull: { early: 0.50, late: 0.25 },   // ~50% early, ~25% late
  };
  const r = rates[scenario];
  // Linear taper between early and late over 10 years
  const t = Math.min(yearsIn / 10, 1);
  return r.early * (1 - t) + r.late * t;
}

// Monthly growth factor from annualised rate
function monthlyFactor(annualRate: number): number {
  return Math.pow(1 + annualRate, 1 / 12);
}

// SteadyStack fee-savings edge per profile (backed by 330-week backtest).
// These represent estimated transaction fee savings from mempool-aware timing,
// NOT price-timing alpha. Values will increase as on-chain fees rise.
export const SS_EDGE_BY_PROFILE: Record<string, number> = {
  conservative: 0.005,  // ~0.5% fee savings
  balanced: 0.01,       // ~1.0% fee savings
  aggressive: 0.015,    // ~1.5% fee savings
};

export function computeProjection(
  monthlyAmount: number,
  durationYears: number,
  ssEdge: number = 0.01
): { points: ProjectionPoint[]; summary: ProjectionSummary } {
  const totalMonths = durationYears * 12;
  const points: ProjectionPoint[] = [];

  // Track BTC price per scenario
  let priceBear = BTC_START_PRICE;
  let priceBase = BTC_START_PRICE;
  let priceBull = BTC_START_PRICE;

  // Track accumulated BTC
  let btcBear = 0;
  let btcBase = 0;
  let btcBull = 0;
  let btcBearSS = 0;
  let btcBaseSS = 0;
  let btcBullSS = 0;

  for (let m = 1; m <= totalMonths; m++) {
    const yearsIn = m / 12;

    // Advance price by one month's growth
    priceBear *= monthlyFactor(annualGrowthRate("bear", yearsIn));
    priceBase *= monthlyFactor(annualGrowthRate("base", yearsIn));
    priceBull *= monthlyFactor(annualGrowthRate("bull", yearsIn));

    // Naive DCA: buy at market price
    btcBear += monthlyAmount / priceBear;
    btcBase += monthlyAmount / priceBase;
    btcBull += monthlyAmount / priceBull;

    // SteadyStack: better cost basis means more BTC per buy
    btcBearSS += (monthlyAmount / priceBear) * (1 + ssEdge);
    btcBaseSS += (monthlyAmount / priceBase) * (1 + ssEdge);
    btcBullSS += (monthlyAmount / priceBull) * (1 + ssEdge);

    // Record quarterly + final month for chart (keeps data manageable)
    if (m % 3 === 0 || m === totalMonths || m === 1) {
      points.push({
        month: m,
        year: parseFloat((m / 12).toFixed(1)),
        totalInvested: monthlyAmount * m,
        bear: { btc: btcBear, usd: btcBear * priceBear },
        base: { btc: btcBase, usd: btcBase * priceBase },
        bull: { btc: btcBull, usd: btcBull * priceBull },
        bearSS: { btc: btcBearSS, usd: btcBearSS * priceBear },
        baseSS: { btc: btcBaseSS, usd: btcBaseSS * priceBase },
        bullSS: { btc: btcBullSS, usd: btcBullSS * priceBull },
      });
    }
  }

  const last = points[points.length - 1];
  return {
    points,
    summary: {
      totalInvested: last.totalInvested,
      bear: last.bear,
      base: last.base,
      bull: last.bull,
      bearSS: last.bearSS,
      baseSS: last.baseSS,
      bullSS: last.bullSS,
    },
  };
}
