"""Support for Transport NSW (AU) to query next leave event."""

from __future__ import annotations

from datetime import timedelta

# from TransportNSW import TransportNSW
from .TransportNSW.TransportNSW import TransportNSW
import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import ATTR_MODE, CONF_API_KEY, CONF_NAME, UnitOfTime, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from .const import ATTR_DELAY, ATTR_DESTINATION, ATTR_DUE_IN, ATTR_REAL_TIME, ATTR_ROUTE, ATTR_STOP_ID, CONF_DESTINATION, CONF_EXCLUDED_MEANS, CONF_ROUTE, CONF_STOP_ID, DEFAULT_NAME, DEFAULT_TIMEOUT, DOMAIN, ICONS, TRANSPORT_MODE_MAP
import logging

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Next Bus"

SCAN_INTERVAL = timedelta(seconds=180)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ROUTE, default=""): cv.string,
        vol.Optional(CONF_DESTINATION, default=""): cv.string,
    }
)

# Legacy?
#async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#    """Set up TransportNSW from configuration file."""
#
#    if DOMAIN not in config:
#        return True
#
#    hass.async_create_task(
#        hass.config_entries.flow.async_init(
#            DOMAIN,
#            context={"source": SOURCE_IMPORT},
#            data=config[DOMAIN]
#        )
#    )
#
#    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up the Transport NSW sensor from a config entry."""

    config = hass.data[DOMAIN][config_entry.entry_id]
    stop_id = config.get(CONF_STOP_ID)
    api_key = config.get(CONF_API_KEY)
    route = config.get(CONF_ROUTE)
    destination = config.get(CONF_DESTINATION)
    name = config.get(CONF_NAME)
    excluded_means = config.get(CONF_EXCLUDED_MEANS)
    timeout = config.get(CONF_TIMEOUT)

    data = PublicTransportData(stop_id, route, destination, api_key, excluded_means, timeout)
    async_add_entities([TransportNSWSensor(hass, data, stop_id, name)], True)

# YAML?
# async def async_setup_platform(
#     hass: HomeAssistant,
#     config: ConfigType,
#     async_add_entities: AddEntitiesCallback,
#     discovery_info: DiscoveryInfoType | None = None,
# ) -> None:
#     """Set up the Transport NSW sensor."""
#     stop_id = config[CONF_STOP_ID]
#     api_key = config[CONF_API_KEY]
#     route = config.get(CONF_ROUTE)
#     destination = config.get(CONF_DESTINATION)
#     name = config.get(CONF_NAME)
#     excluded_means = config.get(CONF_EXCLUDED_MEANS, [])
#     timeout = config.get(CONF_TIMEOUT)
#
#     data = PublicTransportData(stop_id, route, destination, api_key, excluded_means, timeout)
#     async_add_entities([TransportNSWSensor(hass, data, stop_id, name)], True)


class TransportNSWSensor(SensorEntity):
    """Implementation of an Transport NSW sensor."""

    _attr_attribution = "Data provided by Transport NSW"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, data, stop_id, name):
        """Initialize the sensor."""
        super().__init__()
        self._attr_unique_id = name
        self._hass = hass
        self.data = data
        self._name = name
        self._stop_id = stop_id
        self._times = self._state = None
        self._icon = ICONS[None]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self._times is not None:
            return {
                ATTR_DUE_IN: self._times[ATTR_DUE_IN],
                ATTR_STOP_ID: self._stop_id,
                ATTR_ROUTE: self._times[ATTR_ROUTE],
                ATTR_DELAY: self._times[ATTR_DELAY],
                ATTR_REAL_TIME: self._times[ATTR_REAL_TIME],
                ATTR_DESTINATION: self._times[ATTR_DESTINATION],
                ATTR_MODE: self._times[ATTR_MODE],
            }
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return UnitOfTime.MINUTES

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    async def async_update(self) -> None:
        """Get the latest data from Transport NSW and update the states."""
        await self._hass.async_add_executor_job(self.data.update)
        self._times = self.data.info
        self._state = self._times[ATTR_DUE_IN]
        _LOGGER.debug(f"Got mode {self._times[ATTR_MODE]}, attempting to look up icon...")
        self._icon = ICONS[self._times[ATTR_MODE].split(",")[0]]


def _get_value(value):
    """Replace the API response 'n/a' value with None."""
    return None if (value is None or value == "n/a") else value


class PublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(self, stop_id, route, destination, api_key, excluded_means, timeout):
        """Initialize the data object."""
        self._stop_id = stop_id
        self._route = route
        self._destination = destination
        self._excluded_means = excluded_means
        self.info = {
            ATTR_ROUTE: self._route,
            ATTR_DUE_IN: None,
            ATTR_DELAY: None,
            ATTR_REAL_TIME: None,
            ATTR_DESTINATION: None,
            ATTR_MODE: None,
        }
        self.tnsw = TransportNSW(api_key, timeout)

    def update(self):
        """Get the next leave time."""
        _data = self.tnsw.get_trip(
            self._stop_id, self._destination, [k for k, v in TRANSPORT_MODE_MAP.items() if v == self._excluded_means],
        )
        self.info = {
            ATTR_ROUTE: _get_value(_data["route"]),
            ATTR_DUE_IN: _get_value(_data["due"]),
            ATTR_DELAY: _get_value(_data["delay"]),
            ATTR_REAL_TIME: _get_value(_data["real_time"]),
            ATTR_DESTINATION: _get_value(_data["destination"]),
            ATTR_MODE: _get_value(_data["mode"]),
        }
