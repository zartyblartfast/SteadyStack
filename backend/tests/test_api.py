"""Tests for the FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Action, Decision, SignalScore, SignalSnapshot

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self) -> None:
        """Health endpoint returns 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "steadystack"


class TestDecisionEndpoints:
    def _mock_decision(self) -> Decision:
        """Create a mock decision for testing."""
        return Decision(
            action=Action.BUY,
            confidence=0.85,
            reason="BUY — test reason",
            explanation="Test explanation",
            scores=(
                SignalScore(name="fees", value=0.9, weight=0.4, reason="Low fees"),
                SignalScore(name="price", value=0.7, weight=0.35, reason="Good price"),
                SignalScore(name="volatility", value=0.8, weight=0.25, reason="Calm"),
            ),
            snapshot=SignalSnapshot(
                price_usd=65000.0,
                fee_rate_sat_vb=12.0,
                volatility_24h_pct=1.2,
                price_7d_avg=65200.0,
                mempool_depth_mb=5.0,
            ),
        )

    @patch("app.api.decisions.run_pipeline", new_callable=AsyncMock)
    def test_run_decision_success(self, mock_pipeline: AsyncMock) -> None:
        """POST /api/decisions/run returns a valid decision."""
        mock_pipeline.return_value = self._mock_decision()

        response = client.post(
            "/api/decisions/run",
            json={"profile_name": "balanced"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["action"] == "buy"
        assert data["confidence"] == 0.85
        assert len(data["scores"]) == 3
        assert data["explanation"] == "Test explanation"
        assert data["snapshot_summary"]["price_usd"] == 65000.0
        assert data["snapshot_summary"]["fee_rate_sat_vb"] == 12.0

    def test_run_decision_invalid_profile(self) -> None:
        """POST /api/decisions/run rejects unknown profile names."""
        response = client.post(
            "/api/decisions/run",
            json={"profile_name": "nonexistent"},
        )
        assert response.status_code == 400
        assert "Unknown profile" in response.json()["detail"]

    def test_list_profiles(self) -> None:
        """GET /api/decisions/profiles returns all presets."""
        response = client.get("/api/decisions/profiles")
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        assert "conservative" in data["profiles"]
        assert "balanced" in data["profiles"]
        assert "aggressive" in data["profiles"]

        balanced = data["profiles"]["balanced"]
        assert "fee_threshold_low" in balanced
        assert "buy_score_threshold" in balanced
        assert "weight_fee" in balanced
