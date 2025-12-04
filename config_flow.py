import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, URL

class BrugFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["brug"], data=user_input)

        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as r:
                data = await r.json()

        bruggen = {f"{item['id']} – {item['naam']}": item["id"] for item in data}

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(bruggen.keys()))
        })

        self._brug_dict = bruggen
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_create_entry(self, title, data):
        # Koppel naam weer aan ID
        brug_key = data["brug"]
        brug_id = self._brug_dict[brug_key]
        return super().async_create_entry(
            title=title,
            data={"brug_id": brug_id, "brug_naam": brug_key}
        )
