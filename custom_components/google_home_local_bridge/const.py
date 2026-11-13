from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "google_home_local_bridge"
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH]

CONF_AUTH_MODE = "auth_mode"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

AUTH_MODE_LOCAL = "local"
AUTH_MODE_CLOUD = "cloud"

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 8443
DEFAULT_TIMEOUT = 10

DEVICE_TYPE_CLIMATE = "climate"
DEVICE_TYPE_SENSOR = "sensor"
DEVICE_TYPE_SWITCH = "switch"
