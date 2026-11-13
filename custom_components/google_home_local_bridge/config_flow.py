from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import AuthenticationError, ConnectionError, GoogleHomeBridgeApi
from .const import (
    AUTH_MODE_CLOUD,
    AUTH_MODE_LOCAL,
    CONF_ACCESS_TOKEN,
    CONF_AUTH_MODE,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    CONF_PORT,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class GoogleHomeBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            mode = user_input[CONF_AUTH_MODE]
            if mode == AUTH_MODE_LOCAL:
                return await self.async_step_local()
            return await self.async_step_cloud()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AUTH_MODE, default=AUTH_MODE_CLOUD): vol.In(
                        {AUTH_MODE_LOCAL: "Local API", AUTH_MODE_CLOUD: "Cloud API"}
                    )
                }
            ),
        )

    async def async_step_local(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            api = GoogleHomeBridgeApi(
                auth_mode=AUTH_MODE_LOCAL,
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
            )
            try:
                await api.async_get_devices()
            except (ConnectionError, AuthenticationError):
                errors["base"] = "cannot_connect"
            else:
                await api.close()
                return self.async_create_entry(
                    title=f"Google Home Local ({user_input[CONF_HOST]})",
                    data={
                        CONF_AUTH_MODE: AUTH_MODE_LOCAL,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_cloud(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            api = GoogleHomeBridgeApi(
                auth_mode=AUTH_MODE_CLOUD,
                access_token=user_input[CONF_ACCESS_TOKEN],
                refresh_token=user_input.get(CONF_REFRESH_TOKEN),
                client_id=user_input.get(CONF_CLIENT_ID),
                client_secret=user_input.get(CONF_CLIENT_SECRET),
            )
            try:
                await api.async_get_devices()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await api.close()
                return self.async_create_entry(
                    title="Google Home Cloud",
                    data={
                        CONF_AUTH_MODE: AUTH_MODE_CLOUD,
                        CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                        CONF_REFRESH_TOKEN: user_input.get(CONF_REFRESH_TOKEN),
                        CONF_CLIENT_ID: user_input.get(CONF_CLIENT_ID),
                        CONF_CLIENT_SECRET: user_input.get(CONF_CLIENT_SECRET),
                    },
                )

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): str,
                    vol.Optional(CONF_REFRESH_TOKEN): str,
                    vol.Optional(CONF_CLIENT_ID): str,
                    vol.Optional(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GoogleHomeBridgeOptionsFlow(config_entry)


class GoogleHomeBridgeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int
                }
            ),
        )
