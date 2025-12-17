import aiohttp
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, URL, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup van de binary sensor via UI-configuratie."""
    brug_id = entry.data["brug_id"]
    brug_naam = entry.data["brug_naam"]

    coordinator = BrugCoordinator(hass, brug_id)
    await coordinator.async_config_entry_first_refresh()

    sensor = BrugBinarySensor(coordinator, brug_naam, entry.entry_id, brug_id)
    async_add_entities([sensor], True)


class BrugCoordinator(DataUpdateCoordinator):
    """Coordinator die elke SCAN_INTERVAL sec de brugstatus verwerkt."""

    def __init__(self, hass, brug_id):
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=f"brugmelding_{brug_id}",
            update_interval=SCAN_INTERVAL,  # LET OP: SCAN_INTERVAL is nu timedelta
        )
        self.brug_id = brug_id
        self._last_data = None

    def _use_last_data(self, reason: str):
        """Geef de laatst bekende data terug of markeer update als mislukt."""
        if self._last_data is not None:
            _LOGGER.debug(
                "Geen nieuwe data voor brug %s (%s); gebruik laatst bekende status",
                self.brug_id,
                reason,
            )
            return self._last_data
        raise UpdateFailed(reason)

    async def _async_update_data(self):
        """Haalt de meest recente brugstatus op."""
        _LOGGER.debug("Brugmelding: ophalen JSON van %s", URL)

        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                try:
                    resp.raise_for_status()
                    data = await resp.json()
                except Exception as e:
                    _LOGGER.error("JSON decode fout: %s", e)
                    return self._use_last_data(f"JSON fout: {e}")

        # Zoek juiste brug-ID in de lijst
        for b in data:
            if isinstance(b, dict) and b.get("Id") == self.brug_id:
                bridge_data = b.get("Data") or {}
                if bridge_data.get("open") is None:
                    _LOGGER.warning(
                        "Geen status beschikbaar voor brug %s in laatste update",
                        self.brug_id,
                    )
                    return self._use_last_data("Status ontbreekt in feed")
                self._last_data = b
                _LOGGER.debug("Gevonden brug %s: %s", self.brug_id, b)
                return b

        _LOGGER.warning("Brug ID %s niet gevonden in JSON", self.brug_id)
        return self._use_last_data("Brug ID niet gevonden")


class BrugBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor die open/dicht status van één brug weergeeft."""

    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, coordinator, naam, entry_id, brug_id):
        super().__init__(coordinator)
        self._brug_id = brug_id
        self._naam = naam

        self._attr_name = naam
        self._attr_unique_id = f"brugmelding_binary_sensor_{entry_id}"

        # Device info → zodat dit een apparaat wordt in HA
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=naam,
            manufacturer="SvenKopp.nl",
            model="Brug Status Binary Sensor",
            configuration_url="https://brugmelding.svenkopp.com",
        )

    @property
    def is_on(self):
        """Retourneer open/dicht status (True/False)."""
        data = self.coordinator.data
        if not data:
            return None

        d = data.get("Data", {})
        return d.get("open")

    @property
    def entity_picture(self):
        """Gebruik het icoon vanuit /local/brugmelding/icon.png."""
        return "/local/brugmelding/icon.png"

    @property
    def icon(self):
        """Toon verschillend icoon voor open/dicht."""
        data = self.coordinator.data
        status = None

        if data:
            status = data.get("Data", {}).get("open")

        if status is True:
            return "mdi:boom-gate-outline"
        if status is False:
            return "mdi:boom-gate-up-outline"
        return "mdi:boom-gate"

    @property
    def extra_state_attributes(self):
        """Extra informatie uit het JSON Data-blok."""
        data = self.coordinator.data
        if not data:
            return {}

        d = data.get("Data", {})

        return {
            "naam": d.get("Naam"),
            "situatie_huidig": d.get("SituationCurrent"),
            "situatie_voorspeld": d.get("SituationVoorspeld"),
            "ndw_version": d.get("ndwVersion"),
            "datum_start": d.get("GetDatumStart"),
            "image": d.get("image"),
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
        }
