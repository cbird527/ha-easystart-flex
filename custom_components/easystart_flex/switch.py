from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartReadStatusSwitch(coordinator),
    ])

class EasyStartReadStatusSwitch(SwitchEntity):
    """Switch to enable/disable status reading."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart Read Status"
        self._attr_icon = "mdi:monitor"
        self._attr_unique_id = "easystart_read_status"

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
    def is_on(self) -> bool:
        return self._coordinator._connected

    async def async_turn_on(self, **kwargs) -> None:
        await self._coordinator.connect()

    async def async_turn_off(self, **kwargs) -> None:
        await self._coordinator.disconnect()