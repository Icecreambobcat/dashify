import asyncio
import re

from textual.app import App, ComposeResult
from textual.widgets import Button, Digits, Label

from modules.elements import Clock, Stopwatch, TimeDisplay, Timer, TimerDisplay


class ClockApp(App):
    def compose(self) -> ComposeResult:
        yield Clock()
class StopwatchApp(App):
    def compose(self) -> ComposeResult:
        yield Stopwatch()

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
class TestStopwatch:
    def test_layout_and_initial_state(self):
        async def run_test() -> None:
            async with StopwatchApp().run_test() as pilot:
                stopwatch = pilot.app.query_one(Stopwatch)
                display = stopwatch.query_one(TimeDisplay)

                assert display.time == 0.0
                assert display.value == "00:00:00.00"
                assert stopwatch.region.width == 42
                assert stopwatch.region.height == 13
                assert display.size.width == 38
                assert str(stopwatch.query_one(".caption", Label).render()) == "Stopwatch"
                assert not stopwatch.query_one("#reset", Button).disabled

        asyncio.run(run_test())

    def test_start_stop_and_reset(self):
        async def run_test() -> None:
            async with StopwatchApp().run_test() as pilot:
                stopwatch = pilot.app.query_one(Stopwatch)
                display = stopwatch.query_one(TimeDisplay)

                await pilot.click("#start")
                await pilot.pause(0.05)
                assert stopwatch.has_class("started")
                assert stopwatch.query_one("#reset", Button).disabled
                assert display.time > 0.0
                assert display.value != "00:00:00.00"

                await pilot.click("#stop")
                stopped_time = display.time
                await pilot.pause(0.05)
                assert not stopwatch.has_class("started")
                assert not stopwatch.query_one("#reset", Button).disabled
                assert display.time == stopped_time

                await pilot.click("#reset")
                assert display.time == 0.0

        asyncio.run(run_test())
