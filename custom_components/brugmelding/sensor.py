import aiohttp
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, URL, SCAN_INTERVAL


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = BrugCoordinator(hass, entry.data["brug_id"])
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([BrugSensor(coordinator, entry.data["brug_naam"], entry.data["brug_id"])])


class BrugCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, brug_id):
        super().__init__(
            hass,
            name=f"brugmelding_{brug_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.brug_id = brug_id

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                data = await resp.json()
        for brug in data:
            if brug["id"] == self.brug_id:
                return brug
        return None


class BrugSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, naam, brug_id):
        super().__init__(coordinator)
        self._brug_id = brug_id
        self._naam = naam
        self._attr_name = f"Brugmelding {naam}"
        self._attr_unique_id = f"brugmelding_{brug_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, brug_id)},
            name=f"Brugmelding {naam}",
            manufacturer="SvenKopp.nl",
            model="Brug Status Sensor",
            configuration_url="https://github.com/svenkopp/brugmelding_HA",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None
        return data.get("open", False)

    @property
    def entity_picture(self):
        # Verwijs naar het icoon dat via HACS in /www/brugmelding/icon.png wordt gezet
        return "/local/brugmelding/icon.png"
