"""Shared entity base."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BrioCoordinator
from .const import DOMAIN


class BrioEntity(CoordinatorEntity[BrioCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BrioCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="BRiO WiL Pool Light",
            manufacturer="CCEI",
            model="BRiO WiL",
        )
