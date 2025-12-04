import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, URL

class BrugmeldingFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            brug_selected = user_input["brug"]
            brug_id = self._brug_map[brug_selected]
            return self.async_create_entry(
                title=brug_selected,
                data={"brug_id": brug_id, "brug_naam": brug_selected},
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                bruggen = await resp.json()

        self._brug_map = {f"{b['naam']} ({b['id']})": b["id"] for b in bruggen}

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(self._brug_map.keys()))
        })

        return self.async_show_form(step_id="user", data_schema=schema)
