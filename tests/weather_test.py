from modules.composer import compose_from_config
from modules.conf import Config
from modules.weather import Weather
from modules.weather_service import WeatherError, WeatherReading, WeatherService


class TestWeatherService:
    def test_fetches_and_normalises_current_conditions(self, monkeypatch):
        responses = iter(
            [
                {
                    "results": [
                        {
                            "name": "Sydney",
                            "admin1": "New South Wales",
                            "country": "Australia",
                            "latitude": -33.87,
                            "longitude": 151.21,
                        }
                    ]
                },
                {
                    "current": {
                        "temperature_2m": 21.4,
                        "apparent_temperature": 20.8,
                        "weather_code": 2,
                        "wind_speed_10m": 13.2,
                    }
                },
            ]
        )
        monkeypatch.setattr(WeatherService, "_request", lambda *_: next(responses))

        assert WeatherService().get_current_weather(
            "Sydney", "metric"
        ) == WeatherReading(
            location="Sydney, New South Wales, Australia",
            temperature=21.4,
            apparent_temperature=20.8,
            wind_speed=13.2,
            weather_code=2,
            units="metric",
        )

    def test_formats_resolved_location(self):
        assert (
            WeatherService._location_name(
                {"name": "Sydney", "admin1": "New South Wales", "country": "Australia"}
            )
            == "Sydney, New South Wales, Australia"
        )

    def test_rejects_a_missing_location(self, monkeypatch):
        monkeypatch.setattr(WeatherService, "_request", lambda *_: {"results": []})

        try:
            WeatherService().get_current_weather("Missing", "metric")
        except WeatherError as error:
            assert str(error) == "Location not found: Missing"
        else:
            raise AssertionError("Expected a missing-location error")


class TestWeather:
    def test_composer_applies_weather_options(self):
        weather = compose_from_config(
            Config.model_validate(
                {
                    "kind": "Weather",
                    "opts": {"location": "Melbourne", "units": "imperial"},
                }
            )
        )

        assert isinstance(weather, Weather)
        assert weather.location == "Melbourne"
        assert weather.units == "imperial"

    def test_invalid_units_are_rejected(self):
        weather = compose_from_config(
            Config.model_validate({"kind": "Weather", "opts": {"units": "kelvin"}})
        )

        assert weather is None

    def test_translates_weather_codes(self):
        assert Weather.weather_label(0) == "Clear"
        assert Weather.weather_label(63) == "Rain"
        assert Weather.weather_label(95) == "Thunderstorm"
