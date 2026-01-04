import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, BASE_URL
from .api import NetflameApi

class NetflameFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            api = NetflameApi(
                user_input["serial"],
                user_input["password"],
                base_url=user_input.get("url")
            )
            try:
                # Validate by calling get_status in executor (blocking)
                await self.hass.async_add_executor_job(api.get_status)
                return self.async_create_entry(
                    title=f"Netflame {user_input['serial']}",
                    data=user_input
                )
            except Exception:
                errors["base"] = "auth"

        schema = vol.Schema({
            vol.Required("serial"): str,
            vol.Required("password"): str,
            vol.Required("url", default=BASE_URL): str,
        })

        # Provide placeholders so title/description from strings.json
        # can be substituted dynamically (and to help detect translation issues)
        placeholders = {
            "device": "Netflame Stove",
            "serial": (user_input or {}).get("serial", ""),
            "url": (user_input or {}).get("url", BASE_URL)
        }

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )
