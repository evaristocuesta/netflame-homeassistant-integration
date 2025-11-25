from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
import logging

from .const import DOMAIN

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
        NetflameTempSensor(api, coordinator, entry),
        NetflameAlarmaSensor(api, coordinator, entry),
    ], True)


class NetflameTempSensor(CoordinatorEntity, SensorEntity):
    """Netflame Temperature Sensor."""
    
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer"

    def __init__(self, api, coordinator, entry):
        """Initialize the temperature sensor."""
        super().__init__(coordinator)
        self.api = api
        self._entry = entry
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Temperature"
        self._attr_unique_id = f"netflame_{serial}_temp"

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
    def native_value(self):
        """Return the temperature value."""
        return self.coordinator.data.get("temperature")


class NetflameAlarmaSensor(CoordinatorEntity, SensorEntity):
    """Netflame Alarm Sensor."""
    
    _attr_icon = "mdi:alert"

    def __init__(self, api, coordinator, entry):
        """Initialize the alarm sensor."""
        super().__init__(coordinator)
        self.api = api
        self._entry = entry
        serial = entry.data.get("serial")
        self._attr_name = f"Netflame {serial} Alarm"
        self._attr_unique_id = f"netflame_{serial}_alarms"

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
    def native_value(self):
        """Return the alarm value."""
        alarms = self.coordinator.data.get("alarms")
        if alarms:
            return alarms.strip()
        return None
