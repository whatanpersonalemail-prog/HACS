from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_TYPE_SENSOR, DOMAIN
from .coordinator import GoogleHomeBridgeCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GoogleHomeBridgeCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [
        GoogleHomeSensor(coordinator, device_id, key)
        for device_id, device in coordinator.data.items()
        if device.device_type == DEVICE_TYPE_SENSOR
        for key in ("temperature", "humidity")
        if key in device.attributes
    ]
    async_add_entities(entities)


class GoogleHomeSensor(CoordinatorEntity[GoogleHomeBridgeCoordinator], SensorEntity):
    def __init__(self, coordinator, device_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key

    @property
    def device(self):
        return self.coordinator.data.get(self._device_id)

    @property
    def name(self) -> str | None:
        base = getattr(self.device, "name", self._device_id) if self.device else self._device_id
        return f"{base} {self._key.title()}"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_{self._key}"

    @property
    def native_value(self):
        return self.device.attributes.get(self._key) if self.device else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "°C" if self._key == "temperature" else "%"
