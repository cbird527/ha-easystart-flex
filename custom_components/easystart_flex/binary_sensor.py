from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartACRunningBinarySensor(coordinator),
    ])

class EasyStartACRunningBinarySensor(BinarySensorEntity):
    """Binary sensor for AC running status."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart AC Running"
        self._attr_icon = "mdi:air-conditioner"
        self._attr_device_class = "running"

    @property
    def is_on(self) -> bool:
        """Return true if AC is running."""
        return self._coordinator.data.get("status") == "Running"