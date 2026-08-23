"""Textual containers and built-in dashboard widgets."""

from datetime import datetime, timedelta, timezone as datetime_timezone
from functools import partial
from math import ceil
from time import monotonic
from zoneinfo import ZoneInfo

from textual import events
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Digits, Label, Static
# Include this declaration in every built-in widget's DEFAULT_CSS to keep the
# dashboard's widgets visually consistent.
WIDGET_FRAME_CSS = """
border: round $primary;
width: 42;
height: 13;
margin: 1;
padding: 1;
"""


# These classes provide expanding meta-containers accessible to the user.
class VBox(Vertical):
    """An expanding vertical container for dashboard elements."""

    elements: list[Container | Widget]

    def compose(self) -> ComposeResult:
        yield from self.elements


class HBox(Horizontal):
    """An expanding horizontal container for dashboard elements."""

    elements: list[Container | Widget]

    def compose(self) -> ComposeResult:
        yield from self.elements


# These classes provide widgets that the user can place and arrange through the meta-containers
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
    }}

    Stopwatch TimeDisplay {{
        width: 38;
        height: 3;
        text-align: center;
    }}

    Stopwatch .controls {{
        width: 1fr;
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

    Stopwatch .controls Button:focus {{
        text-style: none;
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


    """A clickable countdown display that accepts ``HH:MM:SS`` input."""

    can_focus = True
    remaining = reactive(0.0)
    duration = reactive(0.0)
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

    def set_duration(self, seconds: float) -> None:
        """Set a valid countdown duration and leave edit mode."""
        self.duration = seconds
        self.remaining = seconds
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
        self.remaining = self.duration
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
        width: 1fr;
        height: 1;
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
