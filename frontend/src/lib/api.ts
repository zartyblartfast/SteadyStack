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

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
