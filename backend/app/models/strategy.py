"""User strategy configuration model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class UserStrategy(Base):
    __tablename__ = "user_strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    preset: Mapped[str] = mapped_column(
        String(50), default="balanced"
    )  # conservative | balanced | aggressive | custom

    # Budget
    monthly_budget_usd: Mapped[float] = mapped_column(Float, default=100.0)
    min_buy_usd: Mapped[float] = mapped_column(Float, default=10.0)
    max_buy_usd: Mapped[float] = mapped_column(Float, default=500.0)

    # Custom overrides (nullable — None means use preset defaults)
    fee_threshold_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    fee_threshold_mid: Mapped[float | None] = mapped_column(Float, nullable=True)
    fee_threshold_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_dip_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_premium_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_fee: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_volatility: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="strategies")


from app.models.user import User  # noqa: E402
