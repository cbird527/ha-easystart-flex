from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartACRunningBinarySensor(coordinator),
        EasyStartConnectedBinarySensor(coordinator),
    ])

class EasyStartBaseBinarySensor(BinarySensorEntity):
    """Base class for EasyStart binary sensors with device info."""
    def __init__(self, coordinator, name, icon=None, device_class=None):
        self._coordinator = coordinator
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_unique_id = f"easystart_{name.lower().replace(' ', '_')}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "easystart_flex_device")},
            name="Micro-Air EasyStart Flex",
            manufacturer="Micro-Air",
            model="EasyStart Flex",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        return True  # Always show, even if disconnected

class EasyStartACRunningBinarySensor(EasyStartBaseBinarySensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart AC Running", "mdi:air-conditioner", "running")

    @property
    def is_on(self) -> bool:
        return self._coordinator.data.get("status") == "Running"

class EasyStartConnectedBinarySensor(EasyStartBaseBinarySensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Connected", "mdi:bluetooth-connect", "connectivity")

    @property
    def is_on(self) -> bool:
        return self._coordinator._connected