from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .api import NetflameApi
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Netflame from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    username = entry.data["serial"]
    password = entry.data["password"]

    api = NetflameApi(username, password)

    async def _update():
        # All blocking calls run in executor
        status = await hass.async_add_executor_job(api.get_status)
        alarmas = await hass.async_add_executor_job(api.get_alarmas)
        # Merge alarmas into status dict
        status["alarmas"] = alarmas
        return status

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"netflame_{entry.entry_id}",
        update_method=_update,
        update_interval=SCAN_INTERVAL,
    )

    # Refresh once on setup (this will run API calls in executor)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    # Forward setups for platforms (correct HA API)
    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
