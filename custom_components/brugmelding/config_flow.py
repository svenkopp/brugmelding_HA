import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, URL


class BrugmeldingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._brug_map = {}

    async def async_step_user(self, user_input=None):
        # Wanneer gebruiker een brug kiest
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

        # Lijst maken voor dropdown
        self._brug_map = {
            f"{b['naam']} ({b['id']})": b["id"]
            for b in bruggen
        }

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(self._brug_map.keys()))
        })

        return self.async_show_form(step_id="user", data_schema=schema)
