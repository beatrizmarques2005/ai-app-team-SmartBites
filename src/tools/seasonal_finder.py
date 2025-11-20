from datetime import datetime, date

class MealHistory:
    def __init__(self):
        self.meal_data: list[dict] = []

    def data_meal(self, meal_name:str, recipe_id: str, day=None, meal_type=None, eaten_date=None):
        eaten_date = eaten_date or datetime.today().date()
        day = day or eaten_date.strftime("%A")

        self.meal_data.append({
            "meal_name": meal_name,
            "recipe_id": recipe_id,
            "day": day,
            "meal_type": meal_type,
            "date": eaten_date
        })

    def meals_on_date(self, target_date: date):
        return [meal for meal in self.meal_data if meal["date"] == target_date]

    def meals_on_day(self, target_day: str):
        return [meal for meal in self.meal_data if meal["day"] == target_day]

    def count_meal_freq(self):
        freq = {}
        for i in self.meal_data:
            name = i["meal_name"]
            freq[name] = freq.get(name, 0) + 1
        return freq

    def most_frequent_meal(self, top_n = 1):
        freq = self.count_meal_freq()
        list = []
        for name, count in freq.items():
            recipe_ids = list({meal["recipe_id"] for meal in self.meal_data if meal["meal_name"] == name})
            list.append({
                "meal_name": name,
                "recipe_ids": recipe_ids,
                "count": count
            })

        list.sort(key=lambda x: x["count"], reverse=True)
        return list[:top_n]