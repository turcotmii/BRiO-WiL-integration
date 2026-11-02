"""Sequence speed select."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SPEEDS
from .entity import BrioEntity

_SPEED_BY_NAME = {name: s for s, name in SPEEDS.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([BrioSpeedSelect(hass.data[DOMAIN][entry.entry_id])])


class BrioSpeedSelect(BrioEntity, SelectEntity):
    _attr_name = "Sequence speed"
    _attr_icon = "mdi:play-speed"
    _attr_options = list(SPEEDS.values())

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_speed"

    @property
    def current_option(self) -> str | None:
        return SPEEDS.get(self.coordinator.data.speed)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_run(
            self.coordinator.client.async_set_speed(_SPEED_BY_NAME[option])
        )
