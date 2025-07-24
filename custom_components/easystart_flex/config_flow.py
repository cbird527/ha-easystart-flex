from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN

class EasyStartFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for EasyStart Flex."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="EasyStart Flex", data={"mac": user_input["mac"]})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("mac"): str}),
            description_placeholders={"desc": "Enter the Bluetooth MAC address of your EasyStart Flex (from the app)."}
        )