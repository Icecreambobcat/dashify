"""Live weather widget backed by Open-Meteo."""

from textual import work
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Button, Label, Static

from modules.elements import WIDGET_FRAME_CSS
from modules.weather_service import WeatherError, WeatherReading, WeatherService


class Weather(VerticalGroup):
    """Display current conditions with automatic and manual refreshes."""

    location = "Sydney"
    units = "metric"
    refresh_minutes = 15

    DEFAULT_CSS = f"""
    Weather {{ {WIDGET_FRAME_CSS} align: center middle; }}
    Weather .weather-location, Weather .weather-current, Weather .weather-detail, Weather .caption {{ width: 38; text-align: center; }}
    Weather .weather-location, Weather .caption {{ color: $text-muted; }}
    Weather .weather-current {{ text-style: bold; }}
    Weather .weather-error {{ color: $error; text-align: center; width: 38; }}
    Weather .controls {{ width: 38; height: 3; align: center middle; margin: 1 0 0 0; }}
    Weather .controls Button {{ width: 1fr; }}
    Weather .caption {{ text-style: bold; margin: 1 0 0 0; }}
    """

    def compose(self) -> ComposeResult:
        """Compose weather values, refresh control, and caption."""
        yield Label(classes="weather-location", markup=False)
        yield Static("Loading weather…", classes="weather-current", markup=False)
        yield Static(classes="weather-detail", markup=False)
        yield Static(classes="weather-error", markup=False)
        with HorizontalGroup(classes="controls"):
            yield Button("Refresh", id="weather-refresh")
        yield Label("Weather", classes="caption")

    def on_mount(self) -> None:
        """Fetch immediately and schedule the configured refresh interval."""
        self.request_refresh()
        self.set_interval(self.refresh_minutes * 60, self.request_refresh)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Refresh current conditions when the refresh button is pressed."""
        if event.button.id == "weather-refresh":
            self.request_refresh()

    def request_refresh(self) -> None:
        """Render a loading state and fetch weather without blocking Textual."""
        self.query_one(".weather-current", Static).update("Loading weather…")
        self.query_one(".weather-error", Static).update("")
        self.fetch_weather()

    @work(thread=True, exclusive=True)
    def fetch_weather(self) -> None:
        """Fetch weather in a worker thread and apply the result on the UI thread."""
        try:
            reading = WeatherService().get_current_weather(self.location, self.units)
        except WeatherError as error:
            self.app.call_from_thread(self.show_error, str(error))
        else:
            self.app.call_from_thread(self.show_reading, reading)

    def show_reading(self, reading: WeatherReading) -> None:
        """Render a successful weather response."""
        temperature_unit = "°F" if reading.units == "imperial" else "°C"
        wind_unit = "mph" if reading.units == "imperial" else "km/h"
        self.query_one(".weather-location", Label).update(reading.location)
        self.query_one(".weather-current", Static).update(
            f"{reading.temperature:.0f}{temperature_unit} · {self.weather_label(reading.weather_code)}"
        )
        self.query_one(".weather-detail", Static).update(
            f"Feels like {reading.apparent_temperature:.0f}{temperature_unit} · Wind {reading.wind_speed:.0f} {wind_unit}"
        )

    def show_error(self, message: str) -> None:
        """Render a recoverable network or response error."""
        self.query_one(".weather-current", Static).update("Weather unavailable")
        self.query_one(".weather-error", Static).update(message)

    def validate_options(self) -> str | None:
        """Validate Weather-specific option values after generic assignment."""
        if not self.location.strip() or self.units not in {"metric", "imperial"}:
            return "Invalid weather options"
        if self.refresh_minutes <= 0:
            return "Invalid weather options"
        return None

    @staticmethod
    def weather_label(code: int) -> str:
        """Translate common WMO weather codes to concise labels."""
        if code == 0:
            return "Clear"
        if code in {1, 2, 3}:
            return "Cloudy"
        if code in {45, 48}:
            return "Fog"
        if code in {51, 53, 55, 56, 57}:
            return "Drizzle"
        if code in {61, 63, 65, 66, 67, 80, 81, 82}:
            return "Rain"
        if code in {71, 73, 75, 77, 85, 86}:
            return "Snow"
        if code in {95, 96, 99}:
            return "Thunderstorm"
        return "Unknown"
