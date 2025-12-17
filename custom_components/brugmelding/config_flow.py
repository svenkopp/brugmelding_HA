import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, URL


class BrugmeldingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Brugmelding integratie."""

    VERSION = 1

    def __init__(self):
        self._brug_map = {}

    async def async_step_user(self, user_input=None):
        """Start configuratiestap."""
        # Wanneer gebruiker een brug selecteert
        if user_input is not None:
            gekozen = user_input["brug"]
            brug_id = self._brug_map[gekozen]
            return self.async_create_entry(
                title=gekozen,
                data={
                    "brug_id": brug_id,
                    "brug_naam": gekozen
                },
            )

        # Bruggen ophalen vanaf jouw endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as resp:
                    bruggen = await resp.json()
        except Exception:
            return self.async_abort(reason="cannot_connect")

        # Datastructuur verwerken
        valid = []
        for b in bruggen:
            if not isinstance(b, dict):
                continue

            brug_id = b.get("Id")
            data = b.get("Data", {})
            naam = data.get("Naam")

            if brug_id and naam:
                valid.append((naam, brug_id))

        if not valid:
            return self.async_abort(reason="no_bruggen_available")

        # Alfabetisch sorteren op naam
        valid.sort(key=lambda x: x[0].lower())

        # Dropdown-lijst maken
        self._brug_map = {
            f"{naam}": brug_id
            for naam, brug_id in valid
        }

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(self._brug_map.keys()))
        })

        return self.async_show_form(step_id="user", data_schema=schema)
