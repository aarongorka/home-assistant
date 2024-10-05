"""The transport_nsw component."""
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
from .const import ATTR_DELAY, ATTR_DESTINATION, ATTR_DUE_IN, ATTR_REAL_TIME, ATTR_ROUTE, ATTR_STOP_ID, CONF_DESTINATION, CONF_EXCLUDED_MEANS, CONF_ROUTE, CONF_STOP_ID, DEFAULT_NAME, DEFAULT_TIMEOUT, DOMAIN
from .sensor import PublicTransportData

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS: list[str] = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TransportNSW from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
