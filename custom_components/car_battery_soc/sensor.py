from homeassistant.components.sensor import SensorEntity
from homeassistant.util import slugify
from datetime import datetime
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    # Poprawka: teraz pobieramy 'data' z wnętrza słownika 'storage'
    storage = hass.data[DOMAIN][entry.entry_id]
    data = storage["data"]
    car_name = entry.data.get(CONF_NAME)
    
    async_add_entities([
        SocSensor(data, car_name, "Work Time", "soc_work_time", "min", "mdi:clock", entry.entry_id),
        SocSensor(data, car_name, "Starts", "soc_starts", "starty", "mdi:engine", entry.entry_id),
        SocSensor(data, car_name, "Daily Points", "soc_daily_points", "pkt", "mdi:chart-line", entry.entry_id),
        SocSensor(data, car_name, "Battery Health", "soc_battery_health", "pkt", "mdi:battery-heart", entry.entry_id)
    ])

class SocSensor(SensorEntity):
    def __init__(self, data, car_name, label, s_id, unit, icon, entry_id):
        self._data = data
        self._entry_id = entry_id
        self._s_id = s_id
        self._unit = unit
        self._icon = icon
        
        self._attr_name = f"{car_name} SOC {label}"
        self._attr_unique_id = f"{entry_id}_{s_id}"
        self.entity_id = f"sensor.{slugify(car_name)}_{s_id}"

    @property
    def native_value(self):
        # Sprawdzanie czy klucz istnieje (bezpiecznik)
        if self._s_id not in ["soc_work_time", "soc_starts", "soc_daily_points", "soc_battery_health"]:
            return None

        if self._s_id == "soc_work_time":
            total = self._data.get("today_work_time", 0.0)
            if self._data.get("is_on") and self._data.get("start_time"):
                try:
                    diff = (datetime.now() - datetime.fromisoformat(self._data["start_time"])).total_seconds() / 60
                    total += diff
                except:
                    pass
            return round(total, 1)

        if self._s_id == "soc_starts": 
            return self._data.get("today_starts", 0)

        if self._s_id == "soc_daily_points": 
            return round(self._data.get("today_points", 0.0), 1)

        if self._s_id == "soc_battery_health": 
            return round(self._data.get("battery_points", 20.0), 1)

    @property
    def native_unit_of_measurement(self): 
        return self._unit

    @property
    def icon(self): 
        return self._icon

    async def async_added_to_hass(self):
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_{self._entry_id}_update", self._update_callback))

    def _update_callback(self, _=None):
        self.schedule_update_ha_state()
