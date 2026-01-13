from homeassistant.components.select import SelectEntity
from homeassistant.util import slugify
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    storage = hass.data[DOMAIN][entry.entry_id]
    car_name = entry.data.get(CONF_NAME)
    async_add_entities([SocVoltageSelect(storage, car_name, entry.entry_id)])

class SocVoltageSelect(SelectEntity):
    def __init__(self, storage, car_name, entry_id):
        self._storage = storage
        self._data = storage["data"]
        self._entry_id = entry_id
        
        self._attr_name = f"{car_name} Korekta Napięcia (Pomiar)"
        self._attr_unique_id = f"{entry_id}_voltage_select"
        self._attr_icon = "mdi:note-edit-outline"
        self.entity_id = f"select.{slugify(car_name)}_voltage_correction"
        
        self._options_map = {
            "12.80V – 12.95V (Idealny)": 25.0,
            "12.60V – 12.75V (Dobry)": 15.0,
            "12.35V – 12.55V (Niski)": 5.0,
            "Poniżej 12.30V (Krytyczny)": -5.0,
            "Nie wybrano": 0.0 # Opcja domyślna
        }
        self._attr_options = list(self._options_map.keys())

    @property
    def current_option(self):
        """Zwraca ostatnio wybraną opcję z pamięci."""
        return self._data.get("last_voltage_selection", "Nie wybrano")

    async def async_select_option(self, option: str) -> None:
        """Korekta punktów i zapisanie wyboru w pamięci."""
        if option in self._options_map:
            # Nie zmieniaj punktów, jeśli wybrano "Nie wybrano"
            if option != "Nie wybrano":
                new_points = self._options_map[option]
                self._data["battery_points"] = new_points
            
            # Zapisz wybór do pamięci
            self._data["last_voltage_selection"] = option
            
            await self._storage["save"]()
            
            # Odśwież sensory i selecta
            self.hass.bus.async_fire(f"{DOMAIN}_{self._entry_id}_update")
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Nasłuchiwanie na zmiany, aby UI się odświeżało."""
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_{self._entry_id}_update", self._update_callback))

    def _update_callback(self, _=None):
        self.schedule_update_ha_state()
