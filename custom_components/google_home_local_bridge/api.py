from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class GoogleHomeBridgeError(Exception):
    """Base error."""


class AuthenticationError(GoogleHomeBridgeError):
    """Authentication failed."""


class ApiRateLimitError(GoogleHomeBridgeError):
    """Rate limited."""


class ConnectionError(GoogleHomeBridgeError):
    """Connection failed."""


@dataclass
class DeviceState:
    device_id: str
    name: str
    device_type: str
    available: bool = True
    attributes: dict[str, Any] = field(default_factory=dict)


class GoogleHomeBridgeApi:
    def __init__(
        self,
        *,
        auth_mode: str,
        host: str | None = None,
        port: int | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.auth_mode = auth_mode
        self.host = host
        self.port = port
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self._session = session
        self._owns_session = session is None
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    def _base_url(self) -> str:
        if self.auth_mode == "local":
            return f"http://{self.host}:{self.port}"
        return "https://homegraph.googleapis.com/v1"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        session = await self._get_session()
        url = f"{self._base_url()}{path}"
        try:
            async with session.request(
                method, url, headers=self._headers(), timeout=self.timeout, **kwargs
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError("Authentication expired or invalid")
                if response.status == 429:
                    raise ApiRateLimitError("API rate limit exceeded")
                if response.status >= 500:
                    raise ConnectionError(f"Server error: {response.status}")
                if response.status >= 400:
                    text = await response.text()
                    raise GoogleHomeBridgeError(f"API error {response.status}: {text}")
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except aiohttp.ClientError as err:
            raise ConnectionError(f"Connection failed: {err}") from err
        except asyncio.TimeoutError as err:
            raise ConnectionError("Request timed out") from err

    async def async_get_devices(self) -> list[DeviceState]:
        if self.auth_mode == "local":
            data = await self._request("GET", "/devices")
        else:
            data = await self._request("GET", "/devices")
        devices = []
        for item in data.get("devices", []) if isinstance(data, dict) else []:
            devices.append(
                DeviceState(
                    device_id=item["id"],
                    name=item.get("name", item["id"]),
                    device_type=item.get("type", "switch"),
                    available=item.get("available", True),
                    attributes=item.get("attributes", {}),
                )
            )
        return devices

    async def async_set_state(self, device_id: str, state: dict[str, Any]) -> None:
        await self._request("POST", f"/devices/{device_id}/state", json=state)

    async def async_refresh_token(self) -> bool:
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        session = await self._get_session()
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        try:
            async with session.post(
                "https://oauth2.googleapis.com/token", data=payload, timeout=self.timeout
            ) as response:
                if response.status != 200:
                    raise AuthenticationError("Token refresh failed")
                data = await response.json()
                self.access_token = data.get("access_token", self.access_token)
                return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ConnectionError(f"Token refresh connection failed: {err}") from err
