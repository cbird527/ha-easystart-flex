import logging
import asyncio
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection, BleakError
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import async_get_current_platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    mac = entry.data["mac"]
    device = bluetooth.async_ble_device_from_address(hass, mac.upper(), connectable=True)
    if not device:
        raise ConfigEntryNotReady(f"Could not find EasyStart Flex with MAC {mac}")

    coordinator = EasyStartCoordinator(hass, device)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.disconnect()
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

class EasyStartCoordinator:
    def __init__(self, hass: HomeAssistant, device):
        self.hass = hass
        self.device = device
        self.client = None
        self.data = {}
        self._lock = asyncio.Lock()
        self._connected = False
        self._task = None

    async def _poll_loop(self):
        while self._connected:
            await self.update_data()
            await asyncio.sleep(30)

    async def connect(self):
        async with self._lock:
            if self._connected:
                return
            for attempt in range(3):
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
                    # Notify on OAD Image Status (for status/fault updates)
                    await self.client.start_notify("d973f2e4-b19e-11e2-9e96-0800200c9a66", self._handle_notification)
                    # Write to OAD Image Block to enable live mode
                    await self.client.write_gatt_char("d973f2e2-b19e-11e2-9e96-0800200c9a66", bytearray([0x01]))
                    self._task = self.hass.loop.create_task(self._poll_loop())
                    return
                except BleakError as e:
                    _LOGGER.warning(f"Connection attempt {attempt+1} failed: {e} - Retrying in 5s...")
                    await asyncio.sleep(5)
            _LOGGER.error("Failed to connect after retries - Ensure AC is running and provide expanded service screenshot")
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
        _LOGGER.debug("Disconnected - auto-reconnecting")
        self.hass.loop.create_task(self.connect())

    async def _handle_notification(self, sender, data: bytearray):
        if len(data) < 1:
            return
        # Parsing placeholder; adjust with real data from nRF
        status_code = data[0]
        self.data["status"] = {0: "Idle", 1: "Starting", 2: "Running"}.get(status_code, "Unknown")  # Example mapping
        if len(data) >= 2:
            self.data["diag"] = data[1]
        if len(data) >= 4:
            self.data["runtime_hours"] = (data[2] << 8) | data[3]
        if len(data) >= 6:
            self.data["live_current"] = data[4] / 10.0
            self.data["line_frequency"] = data[5]
        if len(data) >= 7:
            self.data["last_start_peak"] = data[6]
        if len(data) >= 8:
            self.data["scpt_delay"] = data[7]
        platform = async_get_current_platform()
        await platform.async_add_entities([])

    async def update_data(self):
        if not self._connected:
            return
        try:
            # Read from OAD Image Identify for totals/faults (placeholder)
            total_starts_bytes = await self.client.read_gatt_char("d973f2e1-b19e-11e2-9e96-0800200c9a66")
            self.data["total_starts"] = int.from_bytes(total_starts_bytes, "big")
            total_faults_bytes = await self.client.read_gatt_char("d973f2e3-b19e-11e2-9e96-0800200c9a66")
            self.data["total_faults"] = int.from_bytes(total_faults_bytes, "big")
        except BleakError as e:
            _LOGGER.warning(f"Update failed: {e}")
        except Exception as e:
            _LOGGER.warning(f"Unexpected error: {e}")