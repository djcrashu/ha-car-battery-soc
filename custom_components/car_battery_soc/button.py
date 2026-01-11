from homeassistant.components.button import ButtonEntity
from homeassistant.util import slugify
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    storage = hass.data[DOMAIN][entry.entry_id]
    car_name = entry.data.get(CONF_NAME)
    
    async_add_entities([
        SocBoostButton(storage, car_name, entry.entry_id)
    ])

class SocBoostButton(ButtonEntity):
    def __init__(self, storage, car_name, entry_id):
        self._storage = storage
        self._data = storage["data"]
        self._entry_id = entry_id
        self._car_name = car_name
        
        self._attr_name = f"{car_name} Naładowano Prostownikiem"
        self._attr_unique_id = f"{entry_id}_boost_button"
        self._attr_icon = "mdi:battery-charging-100"
        self.entity_id = f"button.{slugify(car_name)}_charged"

    async def async_press(self) -> None:
        """Co się dzieje po naciśnięciu przycisku."""
        self._data["battery_points"] = 30.0
        await self._storage["save"]()
        # Powiadom sensory o zmianie, żeby od razu pokazały 30 pkt
        self.hass.bus.async_fire(f"{DOMAIN}_{self._entry_id}_update")
