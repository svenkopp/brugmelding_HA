import aiohttp
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .const import DOMAIN, URL, SCAN_INTERVAL


async def async_setup_entry(hass, entry, async_add_entities):
    brug_id = entry.data["brug_id"]
    brug_naam = entry.data["brug_naam"]

    coordinator = BrugCoordinator(hass, brug_id)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        BrugSensor(coordinator, brug_naam, brug_id)
    ])


class BrugCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, brug_id):
        super().__init__(
            hass,
            name=f"brugmelding_{brug_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.brug_id = brug_id

    async def _async_update_data(self):
        """Haalt status op uit JSON endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                data = await resp.json()

        # Zoek opgegeven brug-ID
        for brug in data:
            if not isinstance(brug, dict):
                continue

            if brug.get("Id") == self.brug_id:
                return brug   # Hele JSON object teruggeven

        return None


class BrugSensor(CoordinatorEntity, SensorEntity):
    """Sensor die open/dicht status van één brug weergeeft."""

    def __init__(self, coordinator, naam, brug_id):
        super().__init__(coordinator)
        self._brug_id = brug_id
        self._naam = naam

        self._attr_name = f"Brugmelding {naam}"
        self._attr_unique_id = f"brugmelding_sensor_{brug_id}"

        # Device info → zodat de sensor onder een apparaat valt
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, brug_id)},
            name=f"Brugmelding {naam}",
            manufacturer="SvenKopp.nl",
            model="Brug Status Sensor",
        )

    @property
    def native_value(self):
        """Retourneert open/dicht status van de brug."""

        data = self.coordinator.data
        if not data:
            return None

        # Nieuwe datastructuur:
        # data["Data"]["open"]
        brug_data = data.get("Data", {})
        return brug_data.get("open")

    @property
    def extra_state_attributes(self):
        """Geef extra info zoals situatie en NDW data."""
        data = self.coordinator.data
        if not data:
            return {}

        d = data.get("Data", {})

        return {
            "naam": d.get("Naam"),
            "situatie": d.get("SituationCurrent"),
            "voorspeld": d.get("SituationVoorspeld"),
            "ndw_version": d.get("ndwVersion"),
            "start": d.get("GetDatumStart"),
            "afbeelding": d.get("image"),
        }

    @property
    def entity_picture(self):
        """Gebruik jouw afbeelding als entiteit-icoon."""
        return "/local/brugmelding/icon.png"
