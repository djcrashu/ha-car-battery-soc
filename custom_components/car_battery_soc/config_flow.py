import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_NAME, CONF_BT_ENTITY, CONF_MAC_ADDR

class CarBatteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # .strip() usuwa spacje z początku i końca
            user_input[CONF_MAC_ADDR] = user_input[CONF_MAC_ADDR].strip().lower()
            user_input[CONF_NAME] = user_input[CONF_NAME].strip()
            
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Hyundai"): str,
                vol.Required(CONF_BT_ENTITY): str,
                vol.Required(CONF_MAC_ADDR): str,
            })
        )
