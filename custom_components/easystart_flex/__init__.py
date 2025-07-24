import logging
import asyncio
from bleak import BleakClient, BleakGATTCharacteristic
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import async_get_current_platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EasyStart Flex from a config entry."""
    mac = entry.data["mac"]
    device = bluetooth.async_ble_device_from_address(hass, mac.upper())
    if not device:
        raise ConfigEntryNotReady(f"Could not find EasyStart Flex with MAC {mac}")

    coordinator = EasyStartCoordinator(hass, device)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.disconnect()
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

class EasyStartCoordinator:
    """Coordinator for EasyStart Flex BLE connection."""
    def __init__(self, hass: HomeAssistant, device):
        self.hass = hass
        self.device = device
        self.client = None
        self.data = {}
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self):
        async with self._lock:
            if self._connected:
                return
            try:
                self.client = BleakClient(self.device.address, timeout=30)
                await self.client.connect()
                self._connected = True
                _LOGGER.info(f"Connected to EasyStart Flex at {self.device.address}")
                # Enable notifications (adapt UUIDs from project)
                await self.client.start_notify("0000fff1-0000-1000-8000-00805f9b34fb", self._handle_notification)
                # Write to enable live mode if needed
                await self.client.write_gatt_char("0000fff2-0000-1000-8000-00805f9b34fb", bytearray([0x01]))
            except Exception as e:
                _LOGGER.error(f"Failed to connect: {e}")
                self._connected = False

    async def disconnect(self):
        if self.client and self._connected:
            await self.client.disconnect()
            self._connected = False

    async def _handle_notification(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Parse BLE notification data (adapted from ESPHome lambdas)."""
        if len(data) < 1:
            return
        status_code = data[0]
        status_text = {
            16: "Idle",
            17: "Starting",
            18: "Running",
            # Add more from project (e.g., faults, diag)
        }.get(status_code, "Unknown")
        self.data["status"] = status_text
        if len(data) >= 2:
            self.data["fault_code"] = data[1]  # Example parsing
        if len(data) >= 4:
            runtime_high = data[2]
            runtime_low = data[3]
            self.data["runtime_hours"] = (runtime_high << 8) | runtime_low
        # Add parsing for live current, frequency, etc., from updated project
        if len(data) >= 6:
            self.data["live_current"] = data[4] / 10.0  # Example scaling
            self.data["line_frequency"] = data[5]
        # Trigger entity updates
        platform = async_get_current_platform()
        await platform.async_add_entities([])  # Refresh if needed; better use DataUpdateCoordinator for polling

    async def update_data(self):
        """Poll for updates if notifications insufficient."""
        await self.connect()
        # Read characteristics as needed (e.g., total starts, faults)
        try:
            total_starts = await self.client.read_gatt_char("0000fff4-0000-1000-8000-00805f9b34fb")
            self.data["total_starts"] = int.from_bytes(total_starts, "big")
            # Add more reads
        except Exception as e:
            _LOGGER.warning(f"Update failed: {e}")