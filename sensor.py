from datetime import timedelta
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .const import DOMAIN, URL

SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, entry, async_add_entities):
    brug_id = entry.data["brug_id"]
    brug_naam = entry.data["brug_naam"]

    coordinator = BrugCoordinator(hass, brug_id)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([BrugSensor(coordinator, brug_naam, brug_id)])


class BrugCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, brug_id):
        super().__init__(
            hass,
            name=f"brugmelding_{brug_id}",
            update_interval=SCAN_INTERVAL
        )
        self.brug_id = brug_id

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                data = await resp.json()

        for item in data:
            if item["id"] == self.brug_id:
                return item

        return None


class BrugSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, naam, brug_id):
        super().__init__(coordinator)
        self._attr_name = f"Brugmelding {naam}"
        self._attr_unique_id = f"brugmelding_{brug_id}"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        return data.get("open", False)
