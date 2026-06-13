"""Campaign repository interfaces and in-memory implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.campaigns.events import CampaignEvent
    from app.campaigns.schemas import Campaign


class CampaignRepositoryError(Exception):
    """Raised when repository operations cannot be completed."""


class CampaignRepository(Protocol):
    """Persistence interface for campaigns and their events."""

    def create_campaign(self, campaign: Campaign) -> None:
        """Persist a new campaign."""
        ...

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        """Return a campaign by id, or None when missing."""
        ...

    def list_campaigns(self) -> tuple[Campaign, ...]:
        """Return all campaigns in stable insertion order."""
        ...

    def update_campaign(self, campaign: Campaign) -> None:
        """Replace an existing campaign by id."""
        ...

    def add_event(self, event: CampaignEvent) -> None:
        """Persist an event for an existing campaign."""
        ...

    def list_events(self, campaign_id: str) -> tuple[CampaignEvent, ...]:
        """Return events for a campaign in insertion order."""
        ...


class InMemoryCampaignRepository:
    """In-memory repository for tests and early API wiring.

    This intentionally mirrors the future durable repository contract while
    avoiding database decisions in the first campaign-domain slice.
    """

    def __init__(self) -> None:
        self._campaigns: dict[str, Campaign] = {}
        self._events: dict[str, list[CampaignEvent]] = {}

    def create_campaign(self, campaign: Campaign) -> None:
        """Persist a new campaign, rejecting duplicate ids."""
        if campaign.id in self._campaigns:
            raise CampaignRepositoryError(f"Campaign already exists: {campaign.id}")
        self._campaigns[campaign.id] = campaign
        self._events.setdefault(campaign.id, [])

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        """Return a campaign by id, or None when missing."""
        return self._campaigns.get(campaign_id)

    def list_campaigns(self) -> tuple[Campaign, ...]:
        """Return campaigns in insertion order."""
        return tuple(self._campaigns.values())

    def update_campaign(self, campaign: Campaign) -> None:
        """Replace an existing campaign by id."""
        if campaign.id not in self._campaigns:
            raise CampaignRepositoryError(f"Campaign not found: {campaign.id}")
        self._campaigns[campaign.id] = campaign
        self._events.setdefault(campaign.id, [])

    def add_event(self, event: CampaignEvent) -> None:
        """Persist an event for an existing campaign."""
        if event.campaign_id not in self._campaigns:
            raise CampaignRepositoryError(f"Campaign not found: {event.campaign_id}")
        self._events.setdefault(event.campaign_id, []).append(event)

    def list_events(self, campaign_id: str) -> tuple[CampaignEvent, ...]:
        """Return events for a campaign in insertion order."""
        return tuple(self._events.get(campaign_id, ()))
