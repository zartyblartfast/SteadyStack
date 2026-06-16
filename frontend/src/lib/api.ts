const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface SignalScore {
  name: string;
  value: number;
  weight: number;
  reason: string;
}

export interface DecisionResponse {
  action: "buy" | "skip" | "wait";
  confidence: number;
  reason: string;
  explanation: string;
  scores: SignalScore[];
  snapshot_summary: {
    price_usd: number | null;
    fee_rate_sat_vb: number | null;
    fastest_fee: number | null;
    half_hour_fee: number | null;
    hour_fee: number | null;
    economy_fee: number | null;
    volatility_24h_pct: number | null;
    price_7d_avg: number | null;
    mempool_depth_mb: number | null;
  };
}

export interface ProfileConfig {
  fee_threshold_low: number;
  fee_threshold_mid: number;
  fee_threshold_high: number;
  price_dip_pct: number;
  price_premium_pct: number;
  volatility_low: number;
  volatility_high: number;
  weight_fee: number;
  weight_price: number;
  weight_volatility: number;
  buy_score_threshold: number;
  skip_score_threshold: number;
}

export async function runDecision(
  profileName: string = "balanced"
): Promise<DecisionResponse> {
  const res = await fetch(`${API_BASE}/api/decisions/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_name: profileName }),
  });
  if (!res.ok) throw new Error(`Decision API error: ${res.status}`);
  return res.json();
}

export async function getProfiles(): Promise<
  Record<string, ProfileConfig>
> {
  const res = await fetch(`${API_BASE}/api/decisions/profiles`);
  if (!res.ok) throw new Error(`Profiles API error: ${res.status}`);
  const data = await res.json();
  return data.profiles;
}

export interface FeeHistoryEntry {
  avgHeight: number;
  timestamp: number;
  avgFee_0: number;
  avgFee_10: number;
  avgFee_25: number;
  avgFee_50: number;
  avgFee_75: number;
  avgFee_90: number;
  avgFee_100: number;
}

export type FeeHistoryPeriod = "24h" | "3d" | "1w" | "1m" | "3m" | "6m" | "1y" | "2y" | "3y";

export async function fetchFeeHistory(
  period: FeeHistoryPeriod = "1w"
): Promise<FeeHistoryEntry[]> {
  const res = await fetch(`${API_BASE}/api/fees/history/${period}`);
  if (!res.ok) throw new Error(`Fee history API error: ${res.status}`);
  return res.json();
}


export interface MetricsSummaryResponse {
  fetched_at: string | null;
  price_usd: number;
  price_sources: Record<string, unknown>;
  fees: {
    fastest_fee: number;
    half_hour_fee: number;
    hour_fee: number;
    minimum_fee: number;
  };
  network: {
    block_height: number | null;
    hashrate: number | null;
    difficulty: number | null;
    unmined_btc: number | null;
    next_halving_eta: string | null;
  };
  source_names: string[];
  caveats: string[];
}

export interface BmriMetricsResponse {
  fetched_at: string | null;
  full_index: number;
  lite_index: number;
  difference: number | null;
  full_anchors: Record<string, unknown>;
  lite_components: Record<string, unknown>;
  stats: Record<string, unknown>;
  history: Array<{
    date: string;
    price?: number;
    fullIndex?: number;
    liteIndex?: number;
    difference?: number;
  }>;
  source_note: string | null;
}

export interface BitcoinRiskResponse {
  fetched_at: string | null;
  metric: string;
  risk_score: number;
  band: "deep_value" | "value" | "neutral" | "elevated" | "high" | "extreme" | string;
  mvrv_z_score: number | null;
  mvrv: number | null;
  components: Record<string, unknown>;
  history: Array<{
    date: string;
    unixTs?: number;
    mvrv?: number;
    mvrvZScore?: number;
    components?: Record<string, unknown>;
    riskScore?: number;
    band?: string;
  }>;
  sentiment: Record<string, unknown> | null;
  sentiment_status: string | null;
  source: Record<string, unknown>;
  methodology: string | null;
  limitations: string | null;
  data_date: string | null;
  unix_ts: number | null;
}

export async function fetchMetricsSummary(): Promise<MetricsSummaryResponse> {
  const res = await fetch(`${API_BASE}/api/metrics/summary`);
  if (!res.ok) throw new Error(`Metrics summary API error: ${res.status}`);
  return res.json();
}

export async function fetchBmriMetrics(): Promise<BmriMetricsResponse> {
  const res = await fetch(`${API_BASE}/api/metrics/bmri`);
  if (!res.ok) throw new Error(`BMRI metrics API error: ${res.status}`);
  return res.json();
}

export async function fetchBitcoinRisk(): Promise<BitcoinRiskResponse> {
  const res = await fetch(`${API_BASE}/api/metrics/bitcoin-risk`);
  if (!res.ok) throw new Error(`Bitcoin Risk API error: ${res.status}`);
  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
