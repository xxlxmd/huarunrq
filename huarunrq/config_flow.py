"""Config flow for HuaRunRQ integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_entry_flow

DOMAIN = 'huarunrq'

@config_entries.HANDLERS.register(DOMAIN)
class HuaRunRQFlowHandler(config_entries.ConfigFlow):
    """Handle a config flow for HuaRunRQ."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HuaRunRQOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # TODO: Handle input from the user.
            return self.async_create_entry(title="HuaRunRQ", data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required('cno'): str,
            }),
            errors=errors,
        )

class HuaRunRQOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle HuaRunRQ options."""

    def __init__(self, config_entry):
        """Initialize HuaRunRQ options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id='init',
            data_schema=vol.Schema({
                vol.Required('cno', default=self.config_entry.options.get('cno')): str,
            }),
        )