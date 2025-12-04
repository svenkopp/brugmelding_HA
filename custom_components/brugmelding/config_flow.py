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

        # Nieuwe datastructuur verwerken
        valid_bruggen = []
        for b in bruggen:
            if not isinstance(b, dict):
                continue

            brug_id = b.get("Id")
            data = b.get("Data", {})
            brug_naam = data.get("Naam")

            if brug_id and brug_naam:
                valid_bruggen.append((brug_naam, brug_id))

        if not valid_bruggen:
            return self.async_abort(reason="no_bruggen_available")

        # Optielijst maken: “Willem Alexanderbrug (134)”
        self._brug_map = {
            f"{naam} ({bid})": bid
            for naam, bid in valid_bruggen
        }

        schema = vol.Schema({
            vol.Required("brug"): vol.In(list(self._brug_map.keys()))
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema
        )
