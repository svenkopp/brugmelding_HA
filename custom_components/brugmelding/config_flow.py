import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, URL


class BrugmeldingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._brug_map = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            brug_naam = user_input["brug"]
            brug_id = self._brug_map[brug_naam]
            return self.async_create_entry(
                title=brug_naam,
                data={"brug_id": brug_id, "brug_naam": brug_naam},
            )

        # Bruggen ophalen
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as resp:
                    bruggen = await resp.json()
        except Exception:
            return self.async_abort(reason="cannot_connect")

        # Defensief filteren
        valid_bruggen = [
            b for b in bruggen
            if isinstance(b, dict)
            and "id" in b
            and "naam" in b
        ]

        # Check of er überhaupt bruikbare bruggen zijn
        if not valid_bruggen:
            return self.async_abort(reason="no_bruggen_available")

        # Dropdown-opties bouwen
        self._brug_map = {
            f"{b['naam']} ({b['id']})": b["id"]
            for b in valid_bruggen
        }

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(self._brug_map.keys()))
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema
        )
