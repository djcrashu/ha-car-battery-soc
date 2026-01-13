import logging
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_BT_ENTITY, CONF_MAC_ADDR, CONF_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    bt_entity = entry.data.get(CONF_BT_ENTITY)
    mac_addr = str(entry.data.get(CONF_MAC_ADDR)).lower().strip()
    car_name = entry.data.get(CONF_NAME)

    store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_data")
    
    # Inicjalizacja danych z obsługą nowego klucza dla selecta
    data = await store.async_load() or {
        "battery_points": 20.0,
        "today_points": 0.0,
        "today_work_time": 0.0,
        "today_starts": 0,
        "is_on": False,
        "start_time": None,
        "last_voltage_selection": "Nie wybrano" # DODANE
    }

    # Zapewnienie kompatybilności wstecznej (jeśli plik już istniał bez tego klucza)
    if "last_voltage_selection" not in data:
        data["last_voltage_selection"] = "Nie wybrano"

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "data": data,
        "save": lambda: store.async_save(data)
    }

    async def save_and_update():
        await store.async_save(data)
        hass.bus.async_fire(f"{DOMAIN}_{entry.entry_id}_update")

    async def check_bt_state(event):
        new_state = event.data.get("new_state")
        if not new_state: return
        attr_paired = str(new_state.attributes.get("connected_paired_devices", "")).lower()
        attr_not_paired = str(new_state.attributes.get("connected_not_paired_devices", "")).lower()
        car_connected = (mac_addr in attr_paired) or (mac_addr in attr_not_paired)

        if car_connected and not data["is_on"]:
            data["is_on"] = True
            data["today_starts"] += 1
            data["start_time"] = datetime.now().isoformat()
            await save_and_update()
        elif not car_connected and data["is_on"]:
            data["is_on"] = False
            if data["start_time"]:
                diff = datetime.now() - datetime.fromisoformat(data["start_time"])
                minuty = diff.total_seconds() / 60
                data["today_work_time"] += minuty
                if minuty < 10: p = -1
                elif minuty <= 20: p = 1
                elif minuty <= 40: p = 3
                else: p = 6
                data["battery_points"] = max(-30.0, min(30.0, data["battery_points"] + p))
                data["today_points"] += p
            data["start_time"] = None
            await save_and_update()

    async def daily_penalty(now):
        # Rozliczenie o północy (z Twojej wersji)
        penalty = 2.0 if data["today_starts"] == 0 else 0.5
        data["battery_points"] = max(-30.0, data["battery_points"] - penalty)
        data["today_work_time"] = 0
        data["today_starts"] = 0
        data["today_points"] = 0.0
        # last_voltage_selection zostawiamy, aby status w UI nie zniknął
        await save_and_update()

    if data["is_on"]:
        data["is_on"] = False
        data["start_time"] = None
        await save_and_update()

    async_track_state_change_event(hass, [bt_entity], check_bt_state)
    
    # Ustawienie na północ zgodnie z Twoim kodem
    async_track_time_change(hass, daily_penalty, hour=0, minute=0, second=0)

    # Ładujemy sensory, przyciski i listy wyboru
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button", "select"])
    return True
