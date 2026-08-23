import asyncio
import re

from textual.app import App, ComposeResult
from textual.widgets import Button, Digits, Label

from modules import elements
from modules.elements import (
    Clock,
    CpuGraph,
    HBox,
    Stopwatch,
    SystemMonitor,
    TimeDisplay,
    Timer,
    TimerDisplay,
    VBox,
)


class ClockApp(App):
    def compose(self) -> ComposeResult:
        yield Clock()


class StopwatchApp(App):
    def compose(self) -> ComposeResult:
        yield Stopwatch()


class TimerApp(App):
    def compose(self) -> ComposeResult:
        yield Timer()


class SystemMonitorApp(App):
    def compose(self) -> ComposeResult:
        yield SystemMonitor()


class CpuGraphApp(App):
    def compose(self) -> ComposeResult:
        yield CpuGraph()

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


class TestTimerDisplay:
    def test_right_aligned_input_formatting(self):
        assert TimerDisplay.format_digits("") == "00:00:00"
        assert TimerDisplay.format_digits("1") == "00:00:01"
        assert TimerDisplay.format_digits("1234") == "00:12:34"
        assert TimerDisplay.format_digits("123456") == "12:34:56"

    def test_input_validation(self):
        assert TimerDisplay.parse_digits("") is None
        assert TimerDisplay.parse_digits("126060") is None
        assert TimerDisplay.parse_digits("123456") == 45296


class TestTimer:
    def test_layout_and_editing(self):
        async def run_test() -> None:
            async with TimerApp().run_test() as pilot:
                timer = pilot.app.query_one(Timer)
                display = timer.query_one(TimerDisplay)

                assert timer.region.width == 42
                assert timer.region.height == 15
                assert display.size.width == 38
                assert display.value == "00:00:00"
                assert (
                    str(timer.query_one(".hint", Label).render())
                    == "Click digits to edit; <CR> to confirm"
                )
                assert str(timer.query_one(".caption", Label).render()) == "Timer"

                timer.set_duration(1)
                await pilot.click("TimerDisplay")
                assert display.editing
                assert display.has_class("editing")
                assert display.value == "00:00:00"
                assert display.duration == 0

                await pilot.press("1", "2", "3", "4", "5", "6", "enter")
                assert not display.editing
                assert not display.has_class("editing")
                assert display.value == "12:34:56"
                assert display.duration == 45296

        asyncio.run(run_test())


class TestCpuGraph:
    def test_colours_are_threshold_coded(self):
        assert CpuGraph.colour_for(0) == "green"
        assert CpuGraph.colour_for(59.9) == "green"
        assert CpuGraph.colour_for(60) == "yellow"
        assert CpuGraph.colour_for(84.9) == "yellow"
        assert CpuGraph.colour_for(85) == "red"

    def test_keeps_a_widget_width_history(self):
        async def run_test() -> None:
            async with CpuGraphApp().run_test() as pilot:
                graph = pilot.app.query_one(CpuGraph)

                for load in range(40):
                    graph.add_sample(load)

                assert graph.history == list(range(2, 40))
                assert len(graph.render_graph().plain) == 38

        asyncio.run(run_test())


class TestSystemMonitor:
    def test_layout_and_cpu_update(self, monkeypatch):
        async def run_test() -> None:
            monkeypatch.setattr(elements.psutil, "cpu_percent", lambda interval: 72.4)

            async with SystemMonitorApp().run_test() as pilot:
                monitor = pilot.app.query_one(SystemMonitor)
                graph = monitor.query_one(CpuGraph)

                assert monitor.region.width == 42
                assert monitor.region.height == 8
                assert graph.size.width == 38
                assert list(graph.history) == [72.4]
                assert str(monitor.query_one(".cpu-load", Label).render()) == "CPU: 72%"
                assert (
                    str(monitor.query_one(".caption", Label).render())
                    == "System Monitor"
                )

                monitor.update_cpu_load()
                assert list(graph.history) == [72.4, 72.4]

        asyncio.run(run_test())

    def test_invalid_input_is_rejected(self):
        async def run_test() -> None:
            async with TimerApp().run_test() as pilot:
                display = pilot.app.query_one(TimerDisplay)

                await pilot.click("TimerDisplay")
                await pilot.press("1", "2", "6", "0", "6", "0", "enter")

                assert display.editing
                assert display.duration == 0
                assert display.has_class("invalid")

        asyncio.run(run_test())

    def test_start_stop_completion_and_reset(self):
        async def run_test() -> None:
            async with TimerApp().run_test() as pilot:
                timer = pilot.app.query_one(Timer)
                display = timer.query_one(TimerDisplay)
                control = timer.query_one("#timer-control", Button)

                timer.set_duration(1)
                await pilot.click("#timer-control")
                await pilot.pause(0.05)
                assert timer.mode == "running"
                assert control.label.plain == "Stop"

                await pilot.click("#timer-control")
                assert timer.mode == "stopped"
                assert control.label.plain == "Start"

                timer.set_duration(1)
                await pilot.click("#timer-control")
                display.end_time = 0.0
                display.update_time()
                assert timer.mode == "complete"
                assert timer.has_class("complete")
                assert control.label.plain == "Reset"
                assert control.variant == "warning"

                await pilot.click("#timer-control")
                assert timer.mode == "stopped"
                assert not timer.has_class("complete")
                assert display.value == "00:00:01"

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
