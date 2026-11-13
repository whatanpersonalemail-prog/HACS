from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_TYPE_SWITCH, DOMAIN
from .coordinator import GoogleHomeBridgeCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GoogleHomeBridgeCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [
        GoogleHomeSwitch(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.device_type == DEVICE_TYPE_SWITCH
    ]
    async_add_entities(entities)


class GoogleHomeSwitch(CoordinatorEntity[GoogleHomeBridgeCoordinator], SwitchEntity):
    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device(self):
        return self.coordinator.data.get(self._device_id)

    @property
    def name(self) -> str | None:
        return getattr(self.device, "name", None) if self.device else None

    @property
    def unique_id(self) -> str:
        return self._device_id

    @property
    def is_on(self) -> bool | None:
        return self.device.attributes.get("state") if self.device else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.api.async_set_state(self._device_id, {"state": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.api.async_set_state(self._device_id, {"state": False})
        await self.coordinator.async_request_refresh()
