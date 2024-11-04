"""Efteling calendar support."""

from __future__ import annotations

import json
import logging

import aiohttp
import dateutil

from homeassistant.components import datetime
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant

CALENDAR_URL = "https://www.efteling.com/service/subscriptions/availability"

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the calendars."""
    add_entities(
        [
            EftelingSubscriptionAvailabilityCalendar(
                True,
                False,
                False,
                "Efteling Abonnement Geldigheid (Classic)",
                "Classic",
            ),
            EftelingSubscriptionAvailabilityCalendar(
                False,
                True,
                False,
                "Efteling Abonnement Geldigheid (Plus)",
                "Plus",
            ),
            EftelingSubscriptionAvailabilityCalendar(
                False,
                False,
                True,
                "Efteling Abonnement Geldigheid (Premium)",
                "Premium",
            ),
        ]
    )


class EftelingSubscriptionAvailabilityCalendar(CalendarEntity):
    """Loads the JSON from the API that the website uses to display events for specific subscription types."""

    def __init__(self, classic, plus, premium, name, type):
        """Create the Efteling subscription calendar."""
        self.classic = classic
        self.plus = plus
        self.premium = premium
        self.type = type

        self._event = None
        self._name = name
        self._offset_reached = False

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return events within a datetime range."""

        async with (
            aiohttp.ClientSession() as session,
            session.get(CALENDAR_URL) as resp,
        ):
            data = json.loads(await resp.text())

        events = []
        for rawDate in data:
            date = dateutil.parser.isoparse(rawDate).date()

            allowsClassic = data[rawDate]["Classic"]
            allowsPlus = data[rawDate]["Plus"]
            allowsPremium = data[rawDate]["Premium"]

            if (
                self.classic
                and allowsClassic
                or self.plus
                and allowsPlus
                or self.premium
                and allowsPremium
            ):
                events.append(
                    CalendarEvent(
                        start=date,
                        end=date + datetime.timedelta(days=1),
                        summary=f"Toegang voor {self.type}",
                    )
                )

        return events
