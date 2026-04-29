"""Decision log model — stores every engine decision for auditability."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=True
    )

    # Decision output
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # buy | skip | wait
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    amount_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Signal scores (stored as JSON for full auditability)
    scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # type: ignore[type-arg]

    # Snapshot inputs (stored as JSON — the exact data that produced this decision)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)  # type: ignore[type-arg]

    # Profile used (stored as JSON — captures exact thresholds at decision time)
    profile_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)  # type: ignore[type-arg]

    # User response (Advisory Mode)
    user_response: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # acknowledged | dismissed | acted_on
    user_responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="decisions")


from app.models.user import User  # noqa: E402
