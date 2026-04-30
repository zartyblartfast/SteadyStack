"""Fee history API — proxies mempool.space block fee-rate data for the frontend chart."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings

router = APIRouter(prefix="/api/fees", tags=["fees"])
logger = logging.getLogger(__name__)

VALID_PERIODS = {"24h", "3d", "1w", "1m", "3m", "6m", "1y", "2y", "3y"}


@router.get("/history/{period}")
async def fee_history(period: str) -> list[dict[str, Any]]:
    """Return historical block fee-rates from mempool.space.

    Each entry contains: avgHeight, timestamp, avgFee_0 … avgFee_100
    representing fee-rate percentiles across blocks in that time bucket.

    Valid periods: 24h, 3d, 1w, 1m, 3m, 6m, 1y, 2y, 3y
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Valid: {', '.join(sorted(VALID_PERIODS))}",
        )

    url = f"{settings.mempool_api_url}/v1/mining/blocks/fee-rates/{period}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=settings.http_timeout)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning("mempool.space fee history HTTP %s", e.response.status_code)
        raise HTTPException(status_code=502, detail="mempool.space returned an error") from e
    except httpx.RequestError as e:
        logger.warning("mempool.space fee history request failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach mempool.space") from e
