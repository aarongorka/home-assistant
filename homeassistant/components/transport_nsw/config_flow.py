"""Config flow for Hello World integration."""
from __future__ import annotations

import logging
from typing import Any

# from TransportNSW import TransportNSW
from .TransportNSW.TransportNSW import TransportNSW
import voluptuous as vol
from homeassistant.const import ATTR_MODE, CONF_API_KEY, CONF_NAME, CONF_TIMEOUT, UnitOfTime
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig
from .const import DOMAIN, CONF_STOP_ID, CONF_ROUTE, CONF_DESTINATION, DEFAULT_NAME, CONF_EXCLUDED_MEANS, DEFAULT_TIMEOUT, TRANSPORT_MODE_MAP

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ROUTE, default=""): cv.string,
        vol.Optional(CONF_DESTINATION, default=""): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(int),
        vol.Optional(CONF_EXCLUDED_MEANS, default=[]): SelectSelector(
            SelectSelectorConfig(options=list(TRANSPORT_MODE_MAP.values()), multiple=True, custom_value=False, sort=True)
        )
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    tnsw = TransportNSW(data[CONF_API_KEY], data[CONF_TIMEOUT])
    await hass.async_add_executor_job(tnsw.get_departures,
            data[CONF_STOP_ID], data[CONF_ROUTE], data[CONF_DESTINATION],
        )
    return {"title": data[CONF_NAME]}

class TransportNswConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """TransportNSW config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
