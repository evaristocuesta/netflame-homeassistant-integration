import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .api import NetflameApi

class NetflameFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            api = NetflameApi(user_input["serial"], user_input["password"])
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
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
