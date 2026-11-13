from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ApiRateLimitError,
    AuthenticationError,
    ConnectionError,
    GoogleHomeBridgeApi,
    GoogleHomeBridgeError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class GoogleHomeBridgeCoordinator(DataUpdateCoordinator[dict[str, object]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: GoogleHomeBridgeApi,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="google_home_local_bridge",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, object]:
        try:
            devices = await self.api.async_get_devices()
        except AuthenticationError as err:
            try:
                await self.api.async_refresh_token()
                devices = await self.api.async_get_devices()
            except GoogleHomeBridgeError as refresh_err:
                raise UpdateFailed(f"Authentication failed: {refresh_err}") from refresh_err
        except ApiRateLimitError as err:
            raise UpdateFailed(f"Rate limited: {err}") from err
        except ConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except GoogleHomeBridgeError as err:
            raise UpdateFailed(f"Update failed: {err}") from err

        return {device.device_id: device for device in devices}
