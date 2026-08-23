import asyncio
import re

from textual.app import App, ComposeResult
from textual.widgets import Button, Digits, Label

from modules.elements import Clock, Stopwatch, TimeDisplay, Timer, TimerDisplay


class ClockApp(App):
    def compose(self) -> ComposeResult:
        yield Clock()
class TestClock:
    def test_has_a_timezone_property(self):
        clock = Clock()
        clock.timezone = "UTC+0"

        assert clock.timezone == "UTC+0"

    def test_layout_and_current_time(self):
        async def run_test() -> None:
            async with ClockApp().run_test() as pilot:
                clock = pilot.app.query_one(Clock)
                clock_digits = clock.query_one(Digits)

                assert clock.region.width == 42
                assert clock.region.height == 13
                assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", clock_digits.value)
                assert clock_digits.size.width == 38
                assert clock_digits.region.x > clock.region.x
                assert re.fullmatch(
                    r"Local \(.+\)",
                    str(clock.query_one(".timezone", Label).render()),
                )
                assert str(clock.query_one(".caption", Label).render()) == "Clock"

        asyncio.run(run_test())
