# Bitcoin Card Fee History + Fee Profile Enhancements

> Specification intended for implementation in the `bitcoin-card` project so SteadyStack can source all Bitcoin metrics from Bitcoin Card.

## 1. Goal

SteadyStack wants Bitcoin Card to be the single Bitcoin metrics provider.

Bitcoin Card is already sufficient for:

- current BTC price
- current fee tiers
- network summary
- BMRI history
- Bitcoin Risk history

Bitcoin Card is not yet sufficient for SteadyStack's fee-optimisation screens because the current app needs richer historical fee distribution data and, later, cadence-aware low-fee recommendations.

This spec defines the missing Bitcoin Card enhancements.

## 2. Required enhancement A: local HTTP fee history endpoint

Add a local HTTP endpoint to the Bitcoin Card dashboard server:

```text
GET /api/fee-history?range=24h|3d|1w|1m|3m|6m|1y|2y|3y
```

The MCP tool `get_fee_history` may also be extended to use the same internal data shape.

### 2.1 Purpose

Provide historical fee distribution data for charting and for estimating realistic low-fee targets.

SteadyStack currently uses mempool.space directly for historical fee-rate bands. This endpoint should replace that direct dependency.

### 2.2 Response shape

```ts
export type FeeHistoryRange =
  | "24h"
  | "3d"
  | "1w"
  | "1m"
  | "3m"
  | "6m"
  | "1y"
  | "2y"
  | "3y";

export interface FeeHistoryBandPoint {
  /** ISO timestamp for the bucket/datapoint. */
  t: string;

  /** Minimum / lowest observed fee for the bucket, sat/vB. */
  minFee: number;

  /** Approximate 10th percentile fee, sat/vB. */
  p10Fee: number;

  /** Approximate 25th percentile fee, sat/vB. */
  p25Fee: number;

  /** Median fee, sat/vB. */
  medianFee: number;

  /** Approximate 75th percentile fee, sat/vB. */
  p75Fee: number;

  /** Approximate 90th percentile fee, sat/vB. */
  p90Fee: number;

  /** Maximum / highest observed fee for the bucket, sat/vB. */
  maxFee: number;
}

export interface FeeHistoryBands {
  range: FeeHistoryRange;
  points: FeeHistoryBandPoint[];
  source: string;
  sourceQuality: string;
  partial: boolean;
  note?: string;
  fetchedAt: string;
}
```

### 2.3 Naming compatibility

SteadyStack can map this shape to its current internal chart fields:

```ts
avgFee_0   <- minFee
avgFee_10  <- p10Fee
avgFee_25  <- p25Fee
avgFee_50  <- medianFee
avgFee_75  <- p75Fee
avgFee_90  <- p90Fee
avgFee_100 <- maxFee
```

Bitcoin Card should use the clearer names above rather than SteadyStack's legacy `avgFee_*` names.

### 2.4 Range semantics

Suggested bucket density:

| Range | Suggested bucket granularity |
| --- | --- |
| `24h` | recent blocks or hourly buckets |
| `3d` | hourly or 2-hour buckets |
| `1w` | hourly or 6-hour buckets |
| `1m` | daily buckets |
| `3m` | daily buckets |
| `6m` | daily or 2-day buckets |
| `1y` | daily or weekly buckets |
| `2y` | daily or weekly buckets |
| `3y` | weekly buckets acceptable |

Exact granularity can vary by data source, but must be documented in `note` when approximate or partial.

### 2.5 Partial data rules

Set `partial: true` when:

- history is still being accumulated locally
- source does not cover the requested range completely
- buckets are sparse or approximate
- long ranges are synthesized from limited samples

When `partial: true`, include a user-facing `note` explaining what is missing.

### 2.6 Source/caveat requirements

Include:

- `source`
- `sourceQuality`
- `fetchedAt`
- `partial`
- optional `note`

The endpoint should not present partial/sparse data as authoritative.

## 3. Required enhancement B: fee profile endpoint

Add a second endpoint for app-level fee optimisation:

```text
GET /api/fee-profile?cadence=daily|weekly|monthly&buyAmountUsd=100&targetVbytes=140
```

This can come after `/api/fee-history`, but should be designed against the same data.

### 3.1 Purpose

Provide a realistic low-fee target for a patient DCA campaign.

SteadyStack should not ask normal users to choose arbitrary fee priority tiers. Instead, it should recommend a realistic low-fee sat/vB target based on recent network conditions, cadence, and buy size.

### 3.2 Request parameters

```ts
export type DcaCadence = "daily" | "weekly" | "monthly";

export interface FeeProfileRequest {
  cadence: DcaCadence;

  /** Planned buy amount. Used to express network fee as % of buy. */
  buyAmountUsd: number;

  /** Estimated transaction virtual size. Default 140 vB. */
  targetVbytes?: number;
}
```

HTTP query params:

- `cadence`: required
- `buyAmountUsd`: required
- `targetVbytes`: optional, default `140`

### 3.3 Response shape

```ts
export type FeeRegime = "quiet" | "normal" | "elevated" | "congested" | "extreme";

export interface FeeProfile {
  cadence: DcaCadence;
  buyAmountUsd: number;
  targetVbytes: number;

  /** Recommended realistic low-fee target for this cadence, sat/vB. */
  recommendedSatVb: number;

  /** Estimated network fee at recommended target, USD. */
  estimatedFeeUsd: number;

  /** Estimated fee as percentage of planned buy amount. */
  estimatedFeePctOfBuy: number;

  /** 0.0–1.0 confidence that the target is realistic for the cadence. */
  confidence: number;

  /** Current fee environment. */
  regime: FeeRegime;

  /** Plain-English explanation suitable for UI display. */
  reason: string;

  /** Recent/current fee tiers for context. */
  currentFees: {
    fastestFee: number;
    halfHourFee: number;
    hourFee: number;
    minimumFee: number;
  };

  /** Historical context used to generate the recommendation. */
  historySummary: {
    range: FeeHistoryRange;
    p10Fee: number;
    medianFee: number;
    p90Fee: number;
    partial: boolean;
  };

  source: string;
  sourceQuality: string;
  limitations: string;
  fetchedAt: string;
}
```

### 3.4 Recommendation guidance

Initial algorithm can be simple and transparent:

- daily cadence: lean toward recent p25/median low-fee windows
- weekly cadence: lean toward recent p10/p25 low-fee windows
- monthly cadence: can be more patient, but must avoid unrealistic targets that never confirm
- never blindly recommend `1 sat/vB` if recent history shows it is no longer realistic
- cap/reason about high-fee regimes clearly

Example reason strings:

- `1 sat/vB is realistic for a patient weekly DCA campaign based on recent low-fee windows.`
- `Fees are elevated. 4 sat/vB is the lowest target likely to confirm reliably within a weekly cadence.`
- `Fees are currently congested; consider pausing or requiring review if estimated fees exceed your campaign guardrail.`

## 4. Important product constraints

### 4.1 Fee percent matters

For small DCA amounts, fee cost as a percentage of the buy matters more than sat/vB alone.

Example:

- $5 fee on a $100 buy = 5%
- $5 fee on a $1,000 buy = 0.5%

Bitcoin Card should include enough information for apps to show:

- sat/vB
- estimated fee USD
- estimated fee as % of buy

### 4.2 Do not overpromise confirmation time

Fee estimates are probabilistic. Copy should say `estimated`, `likely`, or `realistic`, not guaranteed.

### 4.3 Keep source transparency

All fee history/recommendation responses should include:

- source
- source quality
- fetched timestamp
- partial/caveat/limitations when applicable

## 5. Acceptance criteria

### 5.1 Fee history endpoint

- `GET /api/fee-history?range=24h` returns 200 with valid `FeeHistoryBands`.
- `GET /api/fee-history?range=1w` returns 200 with valid `FeeHistoryBands`.
- `GET /api/fee-history?range=1m` returns 200 with valid `FeeHistoryBands`.
- Unsupported ranges return 400 with a clear error.
- Every point has numeric `minFee`, `p10Fee`, `p25Fee`, `medianFee`, `p75Fee`, `p90Fee`, `maxFee`.
- `partial` is true when coverage is incomplete.
- `note` explains partial/sparse coverage.
- Response includes `fetchedAt`, `source`, and `sourceQuality`.

### 5.2 Fee profile endpoint

- `GET /api/fee-profile?cadence=weekly&buyAmountUsd=100` returns 200.
- Response includes `recommendedSatVb`, `estimatedFeeUsd`, and `estimatedFeePctOfBuy`.
- `estimatedFeePctOfBuy` is calculated consistently:
  - `estimatedFeeUsd / buyAmountUsd * 100`
- `confidence` is between 0.0 and 1.0.
- `reason` is user-facing plain English.
- High-fee regimes are labelled honestly.
- Invalid/missing `buyAmountUsd` returns 400.

## 6. Tests to add in Bitcoin Card

Suggested tests:

- fee history range validation
- fee history response shape
- percentile band ordering:
  - `minFee <= p10Fee <= p25Fee <= medianFee <= p75Fee <= p90Fee <= maxFee`
- partial long-range behavior
- fee profile buy-size calculation
- fee profile confidence bounds
- 1 sat/vB not always recommended when recent history makes it unrealistic
- source/caveat fields preserved

## 7. SteadyStack migration after Bitcoin Card enhancement

Once Bitcoin Card exposes these endpoints, SteadyStack can:

1. Replace direct `/api/fees/history/{period}` mempool.space proxy with Bitcoin Card `/api/fee-history`.
2. Replace old fee-threshold UI with Bitcoin Card-backed fee profile/recommendation data.
3. Keep fee displays in this order:
   - fee as % of planned buy
   - estimated USD fee
   - sat/vB
4. Remove direct mempool.space dependency from the normal app path.

## 8. Out of scope for first enhancement

Do not include yet:

- exchange execution
- automation decisions
- user-specific campaign state
- wallet/UTXO inspection
- guaranteed confirmation times
- proprietary/opaque scoring

Keep this as transparent Bitcoin network fee data plus a clear low-fee recommendation helper.
