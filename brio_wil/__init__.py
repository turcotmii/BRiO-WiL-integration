"""CCEI BRiO WiL pool light integration (native, no Node-RED)."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BrioClient, BrioError, BrioStatus
from .const import DOMAIN, SCAN_INTERVAL_SECONDS, SETTLE_DELAY

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.LIGHT, Platform.SELECT]


class BrioCoordinator(DataUpdateCoordinator[BrioStatus]):
    """Polls the controller and runs commands."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: BrioClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> BrioStatus:
        try:
            return await self.client.async_get_status()
        except BrioError as err:
            raise UpdateFailed(str(err)) from err

    async def async_run(self, *commands) -> None:
        """Run command coroutines in order, then refresh state."""
        try:
            for i, cmd in enumerate(commands):
                if i:
                    await asyncio.sleep(SETTLE_DELAY)
                await cmd
        except BrioError as err:
            raise UpdateFailed(str(err)) from err
        await asyncio.sleep(SETTLE_DELAY)
        await self.async_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = BrioClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    coordinator = BrioCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok
