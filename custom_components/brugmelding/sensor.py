import aiohttp
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, URL, SCAN_INTERVAL


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup van de sensor via UI-configuratie."""
    brug_id = entry.data["brug_id"]
    brug_naam = entry.data["brug_naam"]

    coordinator = BrugCoordinator(hass, brug_id)
    await coordinator.async_config_entry_first_refresh()

    sensor = BrugSensor(coordinator, brug_naam, brug_id)
    async_add_entities([sensor], True)


class BrugCoordinator(DataUpdateCoordinator):
    """Coordinator die elke 30 sec de JSON ophaalt."""

    def __init__(self, hass, brug_id):
        super().__init__(
            hass,
            name=f"brugmelding_{brug_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.brug_id = brug_id

    async def _async_update_data(self):
        """Verkrijg brug-informatie."""
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                data = await resp.json()

        # Zoek juiste brug op basis van Id
        for b in data:
            if isinstance(b, dict) and b.get("Id") == self.brug_id:
                return b

        return None


class BrugSensor(CoordinatorEntity, SensorEntity):
    """Sensor voor open/dicht status."""

    def __init__(self, coordinator, naam, brug_id):
        super().__init__(coordinator)
        self._brug_id = brug_id
        self._naam = naam

        self._attr_name = f"Brugmelding {naam}"
        self._attr_unique_id = f"brugmelding_sensor_{brug_id}"

        # Device info zodat sensor onder apparaat valt
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, brug_id)},
            name=f"Brugmelding {naam}",
            manufacturer="SvenKopp.nl",
            model="Brug Status Sensor",
        )

    @property
    def native_value(self):
        """Retourneer open/dicht status (True/False)."""
        data = self.coordinator.data
        if not data:
            return None

        d = data.get("Data", {})
        return d.get("open")

    @property
    def entity_picture(self):
        """Icoon voor de entiteit."""
        return "/local/brugmelding/icon.png"

    @property
    def extra_state_attributes(self):
        """Extra attributen uit de JSON."""
        data = self.coordinator.data
        if not data:
            return {}

        d = data.get("Data", {})

        return {
            "naam": d.get("Naam"),
            "situatie": d.get("SituationCurrent"),
            "voorspeld": d.get("SituationVoorspeld"),
            "ndw_version": d.get("ndwVersion"),
            "datum_start": d.get("GetDatumStart"),
            "image": d.get("image"),
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
        }
