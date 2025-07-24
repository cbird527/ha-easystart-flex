from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartStatusSensor(coordinator),
        EasyStartFaultSensor(coordinator),
        EasyStartRuntimeSensor(coordinator),
        # Add more: live current, frequency, total faults/starts, etc.
    ])

class EasyStartStatusSensor(SensorEntity):
    """EasyStart status sensor."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart Status"
        self._attr_icon = "mdi:air-conditioner"

    @property
    def state(self):
        return self._coordinator.data.get("status", "Unknown")

# Similarly for other sensors
class EasyStartFaultSensor(SensorEntity):
    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart Fault Code"

    @property
    def state(self):
        return self._coordinator.data.get("fault_code", "None")

class EasyStartRuntimeSensor(SensorEntity):
    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart Runtime Hours"
        self._attr_unit_of_measurement = "h"
        self._attr_icon = "mdi:clock"

    @property
    def state(self):
        return self._coordinator.data.get("runtime_hours", 0)