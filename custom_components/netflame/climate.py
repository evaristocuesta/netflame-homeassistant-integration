from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Netflame climate from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    coordinator = data["coordinator"]

    async_add_entities([NetflameClimate(api, coordinator, entry)], True)


class NetflameClimate(CoordinatorEntity, ClimateEntity):
    """Netflame Climate Entity."""

    _attr_icon = "mdi:fire"

    def __init__(self, api, coordinator, entry):
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self.api = api
        self._entry = entry
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial}"
        self._attr_unique_id = f"netflame_{serial}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_supported_features = ClimateEntityFeature.PRESET_MODE
        self._attr_preset_modes = [f"Potencia {i}" for i in range(1, 10)]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        serial = self._entry.data.get("serial")
        return DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Netflame {serial}",
            manufacturer="Netflame",
            model="Estufa de Pellets",
            sw_version="1.0",
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data.get("temperatura")

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        estado = self.coordinator.data.get("estado")
        if estado in (0, 1):
            return HVACMode.OFF
        return HVACMode.HEAT

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        if hvac_mode == HVACMode.HEAT:
            await self.hass.async_add_executor_job(self.api.turn_on)
        else:
            await self.hass.async_add_executor_job(self.api.turn_off)
        await self.coordinator.async_request_refresh()

    @property
    def preset_mode(self):
        """Return current preset mode."""
        potencia = self.coordinator.data.get("potencia")
        if potencia:
            return f"Potencia {potencia}"
        return None

    async def async_set_preset_mode(self, preset_mode: str):
        """Set preset mode."""
        try:
            nivel = int(preset_mode.replace("Potencia ", ""))
        except Exception:
            return
        await self.hass.async_add_executor_job(self.api.set_potencia, nivel)
        await self.coordinator.async_request_refresh()
