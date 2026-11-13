from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_TYPE_CLIMATE, DOMAIN
from .coordinator import GoogleHomeBridgeCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GoogleHomeBridgeCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [
        GoogleHomeClimate(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.device_type == DEVICE_TYPE_CLIMATE
    ]
    async_add_entities(entities)


class GoogleHomeClimate(CoordinatorEntity[GoogleHomeBridgeCoordinator], ClimateEntity):
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device(self):
        return self.coordinator.data.get(self._device_id)

    @property
    def name(self) -> str | None:
        return getattr(self.device, "name", None)

    @property
    def unique_id(self) -> str:
        return self._device_id

    @property
    def available(self) -> bool:
        return bool(self.device and self.device.available)

    @property
    def current_temperature(self) -> float | None:
        return self.device.attributes.get("current_temperature") if self.device else None

    @property
    def target_temperature(self) -> float | None:
        return self.device.attributes.get("target_temperature") if self.device else None

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self.device.attributes.get("hvac_mode", "off") if self.device else "off"
        return HVACMode(mode)

    async def async_set_temperature(self, **kwargs) -> None:
        await self.coordinator.api.async_set_state(
            self._device_id, {"target_temperature": kwargs.get("temperature")}
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.api.async_set_state(
            self._device_id, {"hvac_mode": hvac_mode.value}
        )
        await self.coordinator.async_request_refresh()
