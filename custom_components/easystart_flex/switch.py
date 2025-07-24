from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartLiveStatusSwitch(coordinator),
    ])

class EasyStartLiveStatusSwitch(SwitchEntity):
    """Switch to enable/disable live status monitoring."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "EasyStart Live Status"
        self._attr_icon = "mdi:monitor"

    @property
    def is_on(self) -> bool:
        """Return true if live status is on."""
        return self._coordinator._connected  # Or use a specific data key if tracked

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on live monitoring."""
        await self._coordinator.connect()  # Handles connection and enabling notifications

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off live monitoring."""
        await self._coordinator.disconnect()  # Handles disconnection