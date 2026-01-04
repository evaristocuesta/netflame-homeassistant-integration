from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
import logging

from .const import DOMAIN
from .utils import status_svg_data_uri

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Netflame sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    coordinator = data["coordinator"]

    async_add_entities([
        NetflameTempSensor(coordinator, entry),
        NetflameAlarmSensor(coordinator, entry),
        NetflamePowerSensor(coordinator, entry),
        NetflameStatusSensor(coordinator, entry),
    ], True)


class NetflameSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Netflame sensors providing shared device info."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry

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


class NetflameTempSensor(NetflameSensorBase):
    """Netflame Temperature Sensor."""
    
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator, entry):
        """Initialize the temperature sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Temperature"
        self._attr_unique_id = f"netflame_{serial}_temp"

    @property
    def native_value(self):
        """Return the temperature value."""
        return self.coordinator.data.get("temperature")


class NetflameAlarmSensor(NetflameSensorBase):
    """Netflame Alarm Sensor."""
    
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator, entry):
        """Initialize the alarm sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Alarm"
        self._attr_unique_id = f"netflame_{serial}_alarms"

    @property
    def native_value(self):
        """Return the alarm value."""
        alarms = self.coordinator.data.get("alarms")
        
        if alarms:
            return alarms.strip()
        return None
    
    @property
    def icon(self) -> str:
        """Return an icon based on current alarm."""
        alarms = self.coordinator.data.get("alarms")
        if alarms == "N":
            return "mdi:check-circle"

        return "mdi:alert"


class NetflamePowerSensor(NetflameSensorBase):
    """Netflame Power Sensor."""

    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator, entry):
        """Initialize the power sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Power"
        self._attr_unique_id = f"netflame_{serial}_power"

    @property
    def native_value(self):
        """Return the current power setting (int)."""
        return self.coordinator.data.get("power")


class NetflameStatusSensor(NetflameSensorBase):
    """Netflame Status Sensor."""

    _attr_icon = "mdi:fire"

    def __init__(self, coordinator, entry):
        """Initialize the status sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Status"
        self._attr_unique_id = f"netflame_{serial}_status"

    @property
    def native_value(self):
        """Return the numeric status value (0..3)."""
        return self.coordinator.data.get("status")

    @property
    def entity_picture(self) -> str | None:
        """Return a small colored SVG data URI representing the status."""
        status = self.coordinator.data.get("status")
        return status_svg_data_uri(status, size=32)