"""Pool light entity: power, brightness (4 steps) and mode as effect."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_LEVEL, MODES
from .entity import BrioEntity

_MODE_BY_NAME = {name: mode for mode, name in MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([BrioLight(hass.data[DOMAIN][entry.entry_id])])


class BrioLight(BrioEntity, LightEntity):
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(MODES.values())

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_light"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.is_on

    @property
    def brightness(self) -> int | None:
        level = self.coordinator.data.level
        if level is None:
            return None
        return (64, 128, 192, 255)[level]

    @property
    def effect(self) -> str | None:
        return MODES.get(self.coordinator.data.mode)

    async def async_turn_on(self, **kwargs: Any) -> None:
        client = self.coordinator.client
        cmds = []
        if not self.is_on:
            cmds.append(client.async_set_power(True))
        if ATTR_EFFECT in kwargs and kwargs[ATTR_EFFECT] in _MODE_BY_NAME:
            cmds.append(client.async_set_mode(_MODE_BY_NAME[kwargs[ATTR_EFFECT]]))
        if ATTR_BRIGHTNESS in kwargs:
            level = max(0, min(MAX_LEVEL, round(kwargs[ATTR_BRIGHTNESS] / 255 * MAX_LEVEL)))
            cmds.append(client.async_set_level(level))
        if not cmds:
            return
        await self.coordinator.async_run(*cmds)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_run(self.coordinator.client.async_set_power(False))
