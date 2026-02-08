"""
Get Weather action — fetch weather information for a location.
"""

import random
from actions.base import BaseAction


class GetWeatherAction(BaseAction):

    def describe(self):
        return "Get current weather information for a location"

    def examples(self):
        return [
            "what's the weather like",
            "weather in New York",
            "temperature in London",
            "is it going to rain today",
            "forecast for Tokyo",
        ]

    def get_required_fields(self):
        return [
            ("location", "Which city or location?"),
        ]

    def execute(self, details):
        location = details.get("location", "your area")

        summary = f"Get weather for {location}"
        if not self.confirm(summary):
            return False, "Weather check cancelled."

        # Simulated weather data (integrate with OpenWeatherMap API for real data)
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear Skies", "Overcast"]
        condition = random.choice(conditions)
        temp_c = random.randint(5, 35)
        temp_f = round(temp_c * 9 / 5 + 32)
        humidity = random.randint(30, 90)
        wind_speed = random.randint(5, 30)

        result = (
            f"🌤️  Weather for {location.title()}\n"
            f"   Condition: {condition}\n"
            f"   Temperature: {temp_c}°C / {temp_f}°F\n"
            f"   Humidity: {humidity}%\n"
            f"   Wind: {wind_speed} km/h\n"
            f"   (Simulated — integrate with OpenWeatherMap for real data)"
        )
        return True, result
