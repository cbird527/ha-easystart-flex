import logging
import asyncio
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection, BleakError
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import async_get_current_platform

from .const import DOMAIN, SERVICE_UUID  # Add other UUIDs as needed

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EasyStart Flex from a config entry."""
    mac = entry.data["mac"]
    device = bluetooth.async_ble_device_from_address(hass, mac.upper(), connectable=True)
    if not device:
        raise ConfigEntryNotReady(f"Could not find EasyStart Flex with MAC {mac}")

    coordinator = EasyStartCoordinator(hass, device)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    # Defer initial refresh to on-demand (e.g., switch)

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
    """Coordinator for EasyStart Flex BLE connection with auto-reconnect."""
    def __init__(self, hass: HomeAssistant, device):
        self.hass = hass
        self.device = device
        self.client = None
        self.data = {}
        self._lock = asyncio.Lock()
        self._connected = False
        self._task = None

    async def async_config_entry_first_refresh(self):
        pass  # Skip initial; handle on-demand

    async def _poll_loop(self):
        while self._connected:  # Only poll if connected
            await self.update_data()
            await asyncio.sleep(30)  # Poll every 30s for totals

    async def connect(self):
        async with self._lock:
            if self._connected:
                return
            for attempt in range(3):  # Retry 3 times on not found
                try:
                    self.client = await establish_connection(
                        BleakClientWithServiceCache,
                        device=self.device,
                        name="EasyStart Flex",
                        disconnected_callback=self._handle_disconnect,
                        max_attempts=5,
                        use_services_cache=True
                    )
                    self._connected = True
                    _LOGGER.info(f"Connected to EasyStart Flex at {self.device.address}")
                    await self.client.start_notify("0000fff1-0000-1000-8000-00805f9b34fb", self._handle_notification)
                    await self.client.write_gatt_char("0000fff2-0000-1000-8000-00805f9b34fb", bytearray([0x01]))
                    self._task = self.hass.loop.create_task(self._poll_loop())
                    return  # Success
                except BleakError as e:
                    _LOGGER.warning(f"Connection attempt {attempt+1} failed: {e} - Retrying in 5s...")
                    await asyncio.sleep(5)
            _LOGGER.error("Failed to connect after retries - Device may not be powered or UUID mismatch")
            self._connected = False

    async def disconnect(self):
        if self.client and self._connected:
            await self.client.disconnect()
            self._connected = False
        if self._task:
            self._task.cancel()

    @callback
    def _handle_disconnect(self, client):
        self._connected = False
        _LOGGER.debug("Disconnected from EasyStart Flex - attempting auto-reconnect")
        self.hass.loop.create_task(self.connect())  # Auto-reconnect

    async def _handle_notification(self, sender, data: bytearray):
        """Parse BLE notification data."""
        if len(data) < 1:
            return
        status_code = data[0]
        status_text = {16: "Idle", 17: "Starting", 18: "Running"}.get(status_code, "Unknown")
        self.data["status"] = status_text
        if len(data) >= 2:
            self.data["diag"] = data[1]  # Fault/diag code
        if len(data) >= 4:
            self.data["runtime_hours"] = (data[2] << 8) | data[3]
        if len(data) >= 6:
            self.data["live_current"] = data[4] / 10.0  # Scaled current
            self.data["line_frequency"] = data[5]
        if len(data) >= 7:
            self.data["last_start_peak"] = data[6]  # Example; adjust based on testing
        if len(data) >= 8:
            self.data["scpt_delay"] = data[7]
        # Trigger updates
        platform = async_get_current_platform()
        await platform.async_add_entities([])  # Force refresh

    async def update_data(self):
        """Poll for static data."""
        if not self._connected:
            return
        try:
            total_starts_bytes = await self.client.read_gatt_char("0000fff4-0000-1000-8000-00805f9b34fb")
            self.data["total_starts"] = int.from_bytes(total_starts_bytes, "big")
            total_faults_bytes = await self.client.read_gatt_char("0000fff5-0000-1000-8000-00805f9b34fb")
            self.data["total_faults"] = int.from_bytes(total_faults_bytes, "big")
        except BleakError as e:
            _LOGGER.warning(f"Update failed: {e} - Device may not expose this characteristic")
        except Exception as e:
            _LOGGER.warning(f"Unexpected update error: {e}")