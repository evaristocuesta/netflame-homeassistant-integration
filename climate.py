from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVAC_MODE_HEAT, HVAC_MODE_OFF
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator
)

from .const import DOMAIN
from .api import NetflameApi

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_entry(hass, entry, async_add_entities):
    serial = entry.data["serial"]
    password = entry.data["password"]

    api = NetflameApi(serial, password)

    async def _update():
        return await hass.async_add_executor_job(api.get_status)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="netflame",
        update_method=_update,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([NetflameClimate(api, coordinator, serial)])


class NetflameClimate(CoordinatorEntity, ClimateEntity):

    def __init__(self, api, coordinator, name):
        super().__init__(coordinator)
        self.api = api
        self._attr_name = f"Netflame {name}"
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_supported_features = 0
        self._attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def hvac_mode(self):
        estado = self.coordinator.data["estado"]
        if estado in (0, 1):
            return HVAC_MODE_OFF
        return HVAC_MODE_HEAT

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_HEAT:
            await self.hass.async_add_executor_job(self.api.turn_on)
        else:
            await self.hass.async_add_executor_job(self.api.turn_off)

        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        return self.hvac_mode == HVAC_MODE_HEAT
