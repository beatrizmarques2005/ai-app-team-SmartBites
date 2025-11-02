
"""
Calendar Synchronization Tool
-----------------------------

Purpose: Sync meal plan to calendar.

"""
# ----------------------------
# IMPORTS
# ----------------------------

from datetime import datetime, timedelta
from ics import Calendar, Event
from pathlib import Path

# ----------------------------
# CALENDAR SYNC FUNCTIONS
# ----------------------------

# Define default time slots
time_slots = {
    "breakfast": "08:00",
    "lunch": "12:30",
    "dinner": "19:00"
}

def create_calendar_entries(meal_plan: list) -> list:
    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }

    today = datetime.today()
    entries = []

    for item in meal_plan:
        day_name = item.get("day")
        meal_name = item.get("meal")
        meal_time = item.get("time", "dinner")
        offset = weekday_map.get(day_name, 0)
        target_date = today + timedelta(days=(offset - today.weekday()) % 7)

        time_str = time_slots.get(meal_time, "19:00")
        hour, minute = map(int, time_str.split(":"))
        event_datetime = target_date.replace(hour=hour, minute=minute)

        entries.append({
            "title": f"{meal_time.title()} – {meal_name}",
            "datetime": event_datetime,
            "description": f"{meal_name} scheduled for {day_name} at {meal_time}"
        })

    return entries


def export_to_ics(entries: list, filename: str = "calendar.ics") -> bool:

    path = Path(filename).expanduser()
    # if a directory was passed, use default filename inside it
    if path.is_dir():
        path = path / "meal_plan.ics"

    # ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    calendar = Calendar()
    for entry in entries:
        event = Event()
        event.name = entry["title"]
        event.begin = entry["datetime"]
        event.description = entry["description"]
        calendar.events.add(event)

    with path.open("w", encoding="utf-8") as f:
        f.writelines(calendar.serialize_iter())
    return True


