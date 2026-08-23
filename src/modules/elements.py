"""Textual containers and built-in dashboard widgets."""

from datetime import date, datetime, timedelta, timezone as datetime_timezone
from functools import partial
from math import ceil
from pathlib import Path
from time import monotonic
from zoneinfo import ZoneInfo

import psutil
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    ContentSwitcher,
    Digits,
    Input,
    Label,
    OptionList,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

# Include this declaration in every built-in widget's DEFAULT_CSS to keep the
# dashboard's widgets visually consistent.
WIDGET_FRAME_CSS = """
border: round $primary;
width: 42;
height: 13;
margin: 1;
padding: 1;
"""


class VBox(Vertical):
    """An expanding vertical tile for dashboard elements."""

    elements: list[Container | Widget]

    DEFAULT_CSS = """
    VBox {
        width: 1fr;
        height: 1fr;
    }

    VBox .vbox-child {
        width: 1fr;
        height: 1fr;
        margin: 0;
    }
    """

    def compose(self) -> ComposeResult:
        for element in self.elements:
            element.add_class("vbox-child")
            yield element


class HBox(Horizontal):
    """An expanding horizontal layout for bordered dashboard tiles."""

    elements: list[Container | Widget]

    DEFAULT_CSS = """
    HBox {
        width: 1fr;
        height: 1fr;
    }

    HBox .hbox-child {
        width: 1fr;
        height: 1fr;
        margin: 0;
    }
    """

    def compose(self) -> ComposeResult:
        for element in self.elements:
            element.add_class("hbox-child")
            yield element


class InvalidConfig(Static):
    """A warning card occupying the position of an invalid configured element."""

    DEFAULT_CSS = """
    InvalidConfig {
        border: round $warning;
        padding: 1;
        color: $warning;
        content-align: center middle;
        text-align: center;
    }
    """


class TimeDisplay(Digits):
    """A reactive display for a :class:`Stopwatch`'s elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Create a paused timer that updates the display at 60 Hz."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Calculate elapsed time while the stopwatch is running."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Format a changed elapsed time as ``HH:MM:SS.ss``."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Start or resume the stopwatch."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Pause the stopwatch and retain its elapsed time."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        """Reset the stopwatch to zero."""
        self.total = 0.0
        self.time = 0.0


class Stopwatch(VerticalGroup):
    """A compact stopwatch with Start, Stop, and Reset controls.

    The widget has no configuration options yet. Its elapsed time is kept in a
    reactive :class:`TimeDisplay`, so it remains accurate across pauses.
    """

    DEFAULT_CSS = f"""
    Stopwatch {{
        {WIDGET_FRAME_CSS}
        align: center middle;
    }}

    Stopwatch TimeDisplay {{
        width: 38;
        height: 3;
        text-align: center;
    }}

    Stopwatch .controls {{
        width: 38;
        height: 3;
        align: center middle;
        margin: 1 0 0 0;
    }}

    Stopwatch .controls Button {{
        width: 10;
    }}

    Stopwatch .caption {{
        width: 38;
        height: 1;
        margin: 1 0 0 0;
        text-align: center;
        color: $text-muted;
        text-style: bold;
    }}

    Stopwatch #stop {{
        display: none;
    }}

    Stopwatch.started #start {{
        display: none;
    }}

    Stopwatch.started #stop {{
        display: block;
    }}

    """

    def compose(self) -> ComposeResult:
        """Compose the controls and elapsed-time display."""
        yield TimeDisplay()
        with HorizontalGroup(classes="controls"):
            yield Button("Start", id="start", variant="success")
            yield Button("Stop", id="stop", variant="error")
            yield Button("Reset", id="reset")
        yield Label("Stopwatch", classes="caption")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Start, stop, or reset the display for the pressed control."""
        time_display = self.query_one(TimeDisplay)
        reset_button = self.query_one("#reset", Button)

        if event.button.id == "start":
            time_display.start()
            reset_button.disabled = True
            self.add_class("started")
        elif event.button.id == "stop":
            time_display.stop()
            reset_button.disabled = False
            self.remove_class("started")
        elif event.button.id == "reset":
            time_display.reset()


class TimerDisplay(Digits):
    """A clickable countdown display that accepts ``HH:MM:SS`` input."""

    can_focus = True
    end_time: float = 0.0
    remaining = reactive(0.0)
    duration = reactive(0)
    editing = reactive(False)

    def on_mount(self) -> None:
        """Create the paused countdown updater and render zero time."""
        self.update_timer = self.set_interval(1 / 30, self.update_time, pause=True)
        self.render_time()

    def on_click(self, event: events.Click) -> None:
        """Clear the display and enter edit mode when the timer is stopped."""
        timer = self.parent
        if isinstance(timer, Timer) and not timer.is_running:
            timer.prepare_edit()
            self.editing = True
            self.input_digits = ""
            self.update("00:00:00")
            self.focus()
            event.stop()

    def on_key(self, event: events.Key) -> None:
        """Collect right-aligned numeric input while the display is editing."""
        if not self.editing:
            return

        if event.key == "enter":
            self.commit_input()
            event.stop()
        elif event.key == "backspace":
            self.input_digits = self.input_digits[:-1]
            self.render_input()
            event.stop()
        elif event.character is not None and event.character.isdigit():
            self.input_digits = (self.input_digits + event.character)[-6:]
            self.render_input()
            event.stop()

    def set_duration(self, seconds: int) -> None:
        """Set a valid countdown duration and leave edit mode."""
        self.duration = seconds
        self.remaining = float(seconds)
        self.editing = False
        self.render_time()

    def start(self) -> None:
        """Start or resume the countdown."""
        if self.remaining <= 0:
            return
        self.end_time = monotonic() + self.remaining
        self.update_timer.resume()

    def stop(self) -> None:
        """Pause the countdown and retain its remaining time."""
        self.update_timer.pause()
        self.remaining = max(0.0, self.end_time - monotonic())

    def reset(self) -> None:
        """Restore the countdown to its configured duration."""
        self.update_timer.pause()
        self.remaining = float(self.duration)
        self.render_time()

    def update_time(self) -> None:
        """Update the countdown and notify the parent at completion."""
        self.remaining = max(0.0, self.end_time - monotonic())
        if self.remaining == 0.0:
            self.update_timer.pause()
            timer = self.parent
            if isinstance(timer, Timer):
                timer.complete()

    def watch_remaining(self) -> None:
        """Render a changed remaining value outside edit mode."""
        if not self.editing:
            self.render_time()

    def watch_editing(self, editing: bool) -> None:
        """Apply editing styles while accepting a new duration."""
        self.set_class(editing, "editing")

    def render_time(self) -> None:
        """Render remaining time as a whole-second ``HH:MM:SS`` value."""
        self.update(self.format_seconds(ceil(self.remaining)))

    def render_input(self) -> None:
        """Render entered digits right-aligned in an ``HH:MM:SS`` value."""
        self.update(self.format_digits(self.input_digits))

    def commit_input(self) -> None:
        """Accept a valid entered duration or reject an invalid one."""
        seconds = self.parse_digits(self.input_digits)
        timer = self.parent
        if seconds is not None and isinstance(timer, Timer):
            timer.set_duration(seconds)
            return

        self.add_class("invalid")
        self.app.bell()
        self.set_timer(0.5, partial(self.remove_class, "invalid"))

    @staticmethod
    def format_seconds(seconds: int) -> str:
        """Format a number of seconds as ``HH:MM:SS``."""
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_digits(digits: str) -> str:
        """Format up to six right-aligned digits as ``HH:MM:SS``."""
        padded_digits = digits[-6:].rjust(6, "0")
        return f"{padded_digits[:2]}:{padded_digits[2:4]}:{padded_digits[4:]}"

    @staticmethod
    def parse_digits(digits: str) -> int | None:
        """Parse a non-zero, valid ``HH:MM:SS`` digit sequence."""
        padded_digits = digits[-6:].rjust(6, "0")
        hours = int(padded_digits[:2])
        minutes = int(padded_digits[2:4])
        seconds = int(padded_digits[4:])

        if minutes >= 60 or seconds >= 60:
            return None

        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds if total_seconds > 0 else None


class Timer(VerticalGroup):
    """A configurable countdown timer with a single stateful control button."""

    mode = reactive("stopped")

    DEFAULT_CSS = f"""
    Timer {{
        {WIDGET_FRAME_CSS}
        height: 15;
        align: center middle;
    }}

    Timer TimerDisplay {{
        width: 38;
        height: 3;
        text-align: center;
        pointer: pointer;
    }}

    Timer TimerDisplay.editing {{
        background: $primary-muted;
    }}

    Timer .hint,
    Timer .caption {{
        width: 38;
        height: 1;
        text-align: center;
        color: $text-muted;
    }}

    Timer .hint {{
        margin: 1 0 0 0;
    }}

    Timer .caption {{
        margin: 1 0 0 0;
        text-style: bold;
    }}

    Timer .controls {{
        width: 38;
        height: 3;
        align: center middle;
        margin: 1 0 0 0;
    }}

    Timer .controls Button {{
        width: 1fr;
    }}

    Timer.complete {{
        border: round $warning;
    }}

    Timer.complete.flash {{
        border: round $warning 30%;
    }}

    TimerDisplay.invalid {{
        color: $error;
    }}
    """

    @property
    def is_running(self) -> bool:
        """Whether the countdown is currently running."""
        return self.mode == "running"

    def compose(self) -> ComposeResult:
        """Compose the countdown, edit hint, control, and caption."""
        yield TimerDisplay()
        yield Label("Click digits to edit; <CR> to confirm", classes="hint")
        with HorizontalGroup(classes="controls"):
            yield Button("Start", id="timer-control", variant="success")
        yield Label("Timer", classes="caption")

    def on_mount(self) -> None:
        """Create a paused timer used to flash the completion border."""
        self.flash_timer = self.set_interval(
            0.5, lambda: self.toggle_class("flash"), pause=True
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Run the action represented by the single control button."""
        if event.button.id != "timer-control":
            return

        if self.mode == "running":
            self.stop()
        elif self.mode == "complete":
            self.reset()
        else:
            self.start()

    def prepare_edit(self) -> None:
        """Clear the current value and make the stopped timer editable."""
        if self.mode == "complete":
            self.flash_timer.pause()
            self.remove_class("complete", "flash")
        self.mode = "stopped"
        self.query_one(TimerDisplay).set_duration(0)
        self.set_control("Start", "success")

    def set_duration(self, seconds: int) -> None:
        """Store a valid duration supplied by the editable display."""
        self.query_one(TimerDisplay).set_duration(seconds)
        self.mode = "stopped"
        self.set_control("Start", "success")

    def start(self) -> None:
        """Start a configured countdown."""
        display = self.query_one(TimerDisplay)
        if display.remaining <= 0:
            return
        display.start()
        self.mode = "running"
        self.set_control("Stop", "error")

    def stop(self) -> None:
        """Stop the countdown and allow its value to be edited again."""
        self.query_one(TimerDisplay).stop()
        self.mode = "stopped"
        self.set_control("Start", "success")

    def complete(self) -> None:
        """Flash a warning border and present the Reset control."""
        self.mode = "complete"
        self.add_class("complete")
        self.flash_timer.resume()
        self.set_control("Reset", "warning")

    def reset(self) -> None:
        """Restore the completed timer to its configured duration."""
        self.flash_timer.pause()
        self.remove_class("complete", "flash")
        self.query_one(TimerDisplay).reset()
        self.mode = "stopped"
        self.set_control("Start", "success")

    def set_control(self, label: str, variant: str) -> None:
        """Update the label and styling of the single control button."""
        control = self.query_one("#timer-control", Button)
        control.label = label
        control.variant = variant


class CpuGraph(Static):
    """A fixed-width, threshold-coloured history graph of CPU utilisation."""

    BAR_CHARACTERS = "▁▂▃▄▅▆▇█"
    history = reactive(list)

    def add_sample(self, load: float) -> None:
        """Append a CPU percentage and redraw the graph."""
        self.history = [*self.history, max(0.0, min(100.0, load))][-38:]
        self.update(self.render_graph())

    def render_graph(self) -> Text:
        """Render samples as green, yellow, or red bars by utilisation."""
        graph = Text()
        for load in self.history:
            character_index = min(
                len(self.BAR_CHARACTERS) - 1,
                int(load / 100 * len(self.BAR_CHARACTERS)),
            )
            graph.append(
                self.BAR_CHARACTERS[character_index], style=self.colour_for(load)
            )
        return graph

    @staticmethod
    def colour_for(load: float) -> str:
        """Choose an accessible colour for a CPU utilisation threshold."""
        if load < 60:
            return "green"
        if load < 85:
            return "yellow"
        return "red"


class SystemMonitor(VerticalGroup):
    """A compact CPU monitor with a once-per-second colour-coded graph."""

    DEFAULT_CSS = f"""
    SystemMonitor {{
        {WIDGET_FRAME_CSS}
        height: 8;
        align: center middle;
    }}

    SystemMonitor .cpu-load,
    SystemMonitor .caption {{
        width: 38;
        height: 1;
        text-align: center;
    }}

    SystemMonitor .cpu-load {{
        text-style: bold;
    }}

    SystemMonitor CpuGraph {{
        width: 38;
        height: 2;
        text-align: right;
    }}

    SystemMonitor .caption {{
        color: $text-muted;
        text-style: bold;
    }}
    """

    def compose(self) -> ComposeResult:
        """Compose the current CPU reading, history graph, and caption."""
        yield Label(classes="cpu-load")
        yield CpuGraph()
        yield Label("System Monitor", classes="caption")

    def on_mount(self) -> None:
        """Sample immediately, then update CPU utilisation every second."""
        self.update_cpu_load()
        self.set_interval(1, self.update_cpu_load)

    def update_cpu_load(self) -> None:
        """Read the current total CPU utilisation and refresh the card."""
        load = psutil.cpu_percent(interval=None)
        self.query_one(".cpu-load", Label).update(f"CPU: {load:.0f}%")
        self.query_one(CpuGraph).add_sample(load)


class Clock(VerticalGroup):
    """A clock with a large time display, timezone, and caption.

    ``timezone`` defaults to ``"local"``. It may also be ``"UTC"``, a UTC
    offset such as ``"UTC+0"``, or an IANA timezone name such as
    ``"Australia/Sydney"``. The composer can later set this reactive property
    from a Clock widget's TOML ``opts`` table.
    """

    timezone = reactive("local")

    DEFAULT_CSS = f"""
    Clock {{
        {WIDGET_FRAME_CSS}
        align: center middle;
    }}

    Clock Digits {{
        width: 38;
        height: 3;
        text-align: center;
    }}

    Clock .timezone,
    Clock .caption {{
        width: 38;
        height: 1;
        margin: 1 0 0 0;
        text-align: center;
        color: $text-muted;
    }}

    Clock .caption {{
        text-style: bold;
    }}
    """

    def compose(self) -> ComposeResult:
        """Compose the time display and its descriptive labels."""
        yield Digits()
        yield Label(classes="timezone")
        yield Label("Clock", classes="caption")

    def on_mount(self) -> None:
        """Render immediately and schedule once-per-second updates."""
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def watch_timezone(self) -> None:
        """Refresh the display when configuration changes its timezone."""
        if self.is_mounted:
            self.update_clock()

    def update_clock(self) -> None:
        """Render the current time in the configured timezone."""
        self.query_one(Digits).update(
            datetime.now(self._get_timezone()).strftime("%H:%M:%S")
        )
        self.query_one(".timezone", Label).update(self._timezone_label())

    def _timezone_label(self) -> str:
        """Return a descriptive label for the configured timezone."""
        if self.timezone.lower() == "local":
            local_zone = datetime.now().astimezone().tzname() or "local"
            return f"Local ({local_zone})"

        return self.timezone

    def _get_timezone(self) -> datetime_timezone | ZoneInfo | None:
        """Resolve the public timezone string to a datetime timezone object."""
        if self.timezone.lower() == "local":
            return None

        if self.timezone.upper().startswith("UTC"):
            offset = self.timezone[3:]
            if not offset:
                return datetime_timezone.utc
            return datetime_timezone(timedelta(hours=float(offset)))

        return ZoneInfo(self.timezone)
