from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EasyStartStatusSensor(coordinator),
        EasyStartDiagSensor(coordinator),
        EasyStartRuntimeSensor(coordinator),
        EasyStartLiveCurrentSensor(coordinator),
        EasyStartLineFrequencySensor(coordinator),
        EasyStartLastStartPeakSensor(coordinator),
        EasyStartSCPTDelaySensor(coordinator),
        EasyStartTotalFaultsSensor(coordinator),
        EasyStartTotalStartsSensor(coordinator),
    ])

class EasyStartBaseSensor(SensorEntity):
    """Base class for EasyStart sensors with device info."""
    def __init__(self, coordinator, name, icon=None, unit=None):
        self._coordinator = coordinator
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unit_of_measurement = unit
        self._attr_unique_id = f"easystart_{name.lower().replace(' ', '_')}"

    @property
    def device_info(self) -> DeviceInfo:
        """Group under one device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "easystart_flex_device")},
            name="Micro-Air EasyStart Flex",
            manufacturer="Micro-Air",
            model="EasyStart Flex",
            sw_version="1.0",  // Update if known
        )

    @property
    def available(self) -> bool:
        return self._coordinator._connected

class EasyStartStatusSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Status", "mdi:air-conditioner")

    @property
    def state(self):
        return self._coordinator.data.get("status", "Unknown")

class EasyStartDiagSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Diag")

    @property
    def state(self):
        return self._coordinator.data.get("diag", "None")

class EasyStartRuntimeSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Runtime Hours", "mdi:clock", "h")

    @property
    def state(self):
        return self._coordinator.data.get("runtime_hours", 0)

class EasyStartLiveCurrentSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Live Current", unit="A")

    @property
    def state(self):
        return self._coordinator.data.get("live_current", 0.0)

class EasyStartLineFrequencySensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Line Frequency", unit="Hz")

    @property
    def state(self):
        return self._coordinator.data.get("line_frequency", 0)

class EasyStartLastStartPeakSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Last Start Peak", unit="A")

    @property
    def state(self):
        return self._coordinator.data.get("last_start_peak", 0)

class EasyStartSCPTDelaySensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart SCPT Delay", unit="s")

    @property
    def state(self):
        return self._coordinator.data.get("scpt_delay", 0)

class EasyStartTotalFaultsSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Total Faults")

    @property
    def state(self):
        return self._coordinator.data.get("total_faults", 0)

class EasyStartTotalStartsSensor(EasyStartBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "EasyStart Total Starts")

    @property
    def state(self):
        return self._coordinator.data.get("total_starts", 0)