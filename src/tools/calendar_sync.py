from datetime import datetime, timedelta
from ics import Calendar, Event
from pathlib import Path

time_slots = {
    "breakfast": "08:00",
    "lunch": "12:30",
    "dinner": "19:00"
}

weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }

def create_calendar_entries(meal_plan: list[dict]) -> list[dict]:
    today = datetime.today()
    entries = []

    for item in meal_plan:
        day_name = item.get("day")
        meals = item.get("meals", {})
        target_weekday = weekday_map.get(day_name, today.weekday())
        days_ahead = (target_weekday - today.weekday()) %7
        target_date = today + timedelta(days=days_ahead)

        for meal_time_key, meal_name in meals.items():
            time = time_slots.get(meal_time_key.lower(), "19:00")
            hour, minute = map(int, time.split(":"))
            event_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            entries.append({
                "title": f"{meal_time_key.title()} – {meal_name}",
                "datetime": event_datetime,
                "description": f"{meal_name} scheduled for {day_name} at {meal_time_key}"
            })
    return entries


def export_to_ics(entries: list, filename: str = "calendar.ics") -> Path:

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
    return path


# EXAMPLE USAGE
if __name__ == "__main__":
    weekly_plan = [
        {"day": "Monday", "meals": {"breakfast": "Oatmeal Pancakes", "lunch": "Chicken Salad", "dinner": "Grilled Salmon"}},
        {"day": "Wednesday", "meals": {"lunch": "Rice & Beans"}}
    ]

    entries = create_calendar_entries(weekly_plan)
    ics_file = export_to_ics(entries, "SmartBites_MealPlan.ics")
    print(f"Calendar saved to: {ics_file}")