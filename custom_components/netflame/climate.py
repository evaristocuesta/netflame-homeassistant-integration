from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import quote

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
        self._attr_preset_modes = [f"Power {i}" for i in range(1, 10)]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        serial = self._entry.data.get("serial")
        return DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Netflame {serial}",
            manufacturer="Netflame",
            model="Pellet Stove",
            sw_version="1.0",
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data.get("temperature")

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        estado = self.coordinator.data.get("status")
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
        power = self.coordinator.data.get("power")
        if power:
            return f"Power {power}"
        return None

    async def async_set_preset_mode(self, preset_mode: str):
        """Set preset mode."""
        try:
            nivel = int(preset_mode.replace("Power ", ""))
        except Exception:
            return
        await self.hass.async_add_executor_job(self.api.set_power, nivel)
        await self.coordinator.async_request_refresh()

    @property
    def entity_picture(self) -> str | None:
        """Return a colored SVG data URI representing the unit status.

        The frontend will show `entity_picture` if present; this provides a
        small color indicator that changes with the stove state and power.
        """
        status = self.coordinator.data.get("status")

        # Map status to colors
        if status == 0:
            color = "#9e9e9e"  # Off - gray
        elif status in (1, 2):
            color = "#ff9800"  # Turning on/off - orange
        elif status == 3:
            color = f"#ff0000"   # On - red
        else:
            color = "#9e9e9e"

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
            f'<circle cx="32" cy="32" r="28" fill="{color}"/></svg>'
        )
        return "data:image/svg+xml;utf8," + quote(svg, safe=':/,()?=#&;+-')

    @property
    def icon(self) -> str:
        """Return an icon based on current state as a fallback."""
        status = self.coordinator.data.get("status")
        if status == 3:
            return "mdi:fire"
        if status in (1, 2):
            return "mdi:fire-alert"
        return "mdi:fire-off"
