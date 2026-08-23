"""Open-Meteo data access for Dashify's Weather widget."""

from dataclasses import dataclass
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen


class WeatherError(Exception):
    """Raised when weather data cannot be fetched or interpreted."""


@dataclass(frozen=True)
class WeatherReading:
    """Current weather conditions for a resolved location."""

    location: str
    temperature: float
    apparent_temperature: float
    wind_speed: float
    weather_code: int
    units: str


class WeatherService:
    """Fetch current conditions through Open-Meteo's public APIs."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def get_current_weather(self, location: str, units: str) -> WeatherReading:
        """Resolve a location and return its current weather conditions."""
        location_data = self._request(
            self.GEOCODING_URL, {"name": location, "count": 1}
        )
        results = location_data.get("results")
        if not isinstance(results, list) or not results:
            raise WeatherError(f"Location not found: {location}")
        result = results[0]
        if not isinstance(result, dict):
            raise WeatherError("Invalid location response")

        unit_options = (
            {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph"}
            if units == "imperial"
            else {}
        )
        forecast = self._request(
            self.FORECAST_URL,
            {
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                **unit_options,
            },
        )
        current = forecast.get("current")
        if not isinstance(current, dict):
            raise WeatherError("Invalid weather response")
        try:
            return WeatherReading(
                location=self._location_name(result),
                temperature=float(current["temperature_2m"]),
                apparent_temperature=float(current["apparent_temperature"]),
                wind_speed=float(current["wind_speed_10m"]),
                weather_code=int(current["weather_code"]),
                units=units,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise WeatherError("Invalid weather response") from error

    def _request(self, url: str, parameters: dict[str, object]) -> dict[str, object]:
        try:
            with urlopen(f"{url}?{urlencode(parameters)}", timeout=10) as response:
                payload = json.load(response)
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise WeatherError("Weather service unavailable") from error
        if not isinstance(payload, dict):
            raise WeatherError("Invalid weather response")
        return payload

    @staticmethod
    def _location_name(location: dict[str, object]) -> str:
        """Format the most useful location fields returned by geocoding."""
        parts = [location.get("name"), location.get("admin1"), location.get("country")]
        return ", ".join(str(part) for part in parts if part)
