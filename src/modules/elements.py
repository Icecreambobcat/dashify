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

from modules.todo_store import DEFAULT_TODO_DATABASE_PATH, TodoItem, TodoStore

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

    Timer .controls Button:focus {{
        text-style: none;
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
        self.query_one("#timer-control", Button).active_effect_duration = 0

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


class Spotify(Static): ...


class TodoOptionList(OptionList):
    """An option list with Vim-inspired movement shortcuts."""

    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("g", "first", show=False),
        Binding("G", "last", show=False),
        Binding("l", "select", show=False),
    ]

    def on_show(self) -> None:
        """Receive keyboard navigation whenever the surrounding view opens."""
        self.focus()


class TodoTitleInput(Input):
    """Focus the title field whenever the todo form opens."""

    def on_show(self) -> None:
        """Direct typing to the mandatory field first."""
        self.focus()


class TodoInitialFocusButton(Button):
    """Focus the safe initial button in a confirmation or detail view."""

    def on_show(self) -> None:
        """Make the visible button available to keyboard confirmation."""
        self.focus()


class Todo(VerticalGroup):
    """A persistent todo widget with an in-widget interaction context."""

    BINDINGS = [Binding("escape", "back", "Back", show=False)]

    database_path: Path = DEFAULT_TODO_DATABASE_PATH
    pending_action: str | None = None
    selection_mode: str | None = None
    selected_todo_id: int | None = None

    DEFAULT_CSS = f"""
    Todo {{
        {WIDGET_FRAME_CSS}
        height: 18;
    }}

    Todo.interacting {{
        border: round $warning;
    }}

    Todo ContentSwitcher,
    Todo .todo-view {{
        width: 1fr;
        height: 1fr;
    }}

    Todo .todo-view {{
        padding: 1;
    }}

    Todo .todo-list,
    Todo .todo-menu,
    Todo .todo-selector {{
        height: 1fr;
    }}

    Todo .todo-list {{
        border: tall $border;
        padding: 0 1;
    }}

    Todo .todo-actions {{
        height: auto;
        margin: 1 0 0 0;
    }}

    Todo .todo-actions Button {{
        width: 1fr;
    }}

    Todo .todo-title {{
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }}

    Todo .todo-message,
    Todo .todo-error,
    Todo .todo-key-hint {{
        text-align: center;
    }}

    Todo .todo-key-hint {{
        color: $text-muted;
        height: 1;
        margin: 1 0 0 0;
    }}

    Todo .todo-error {{
        color: $error;
        height: 1;
    }}

    Todo .todo-warning {{
        color: $warning;
        text-style: bold;
        text-align: center;
        border: round $warning;
        padding: 1;
        margin: 1 0;
    }}

    Todo TextArea {{
        height: 6;
        margin: 1 0;
    }}

    Todo .caption {{
        width: 1fr;
        height: 1;
        text-align: center;
        color: $text-muted;
        text-style: bold;
        margin: 1 0 0 0;
    }}
    """

    def compose(self) -> ComposeResult:
        """Compose the summary and every full-widget interaction view."""
        with ContentSwitcher(initial="todo-summary", id="todo-views"):
            with Vertical(id="todo-summary", classes="todo-view"):
                with VerticalScroll(classes="todo-list"):
                    yield Static(id="todo-summary-list")
                with Horizontal(classes="todo-actions"):
                    yield Button("Manage todos", id="todo-manage")

            with Vertical(id="todo-context", classes="todo-view"):
                yield Label("Todo menu", classes="todo-title")
                yield TodoOptionList(
                    Option("Browse todos", id="browse"),
                    Option("Add todo", id="add"),
                    Option("Edit todo", id="edit"),
                    Option("Delete todo", id="delete"),
                    Option("Clear database", id="clear"),
                    Option("Exit", id="exit"),
                    id="todo-menu",
                    classes="todo-menu",
                )
                yield Label(
                    "j/k move · g/G first/last · l/Enter select · Esc back",
                    classes="todo-key-hint",
                )

            with Vertical(id="todo-create-database", classes="todo-view"):
                yield Label("Create todo database?", classes="todo-title")
                yield Static(
                    "No todo database exists. Create one to continue?",
                    classes="todo-message",
                )
                yield TodoOptionList(
                    Option("Yes — create database", id="yes"),
                    Option("No — exit", id="no"),
                    id="todo-create-choice",
                    classes="todo-menu",
                )
                yield Label(
                    "j/k move · g/G first/last · l/Enter select · Esc back",
                    classes="todo-key-hint",
                )

            with Vertical(id="todo-selector", classes="todo-view"):
                yield Label(
                    "Select todo", id="todo-selector-title", classes="todo-title"
                )
                yield TodoOptionList(id="todo-selector-list", classes="todo-selector")
                yield Label(
                    "j/k move · g/G first/last · l/Enter select · Esc back",
                    classes="todo-key-hint",
                )

            with Vertical(id="todo-form", classes="todo-view"):
                yield Label("Add todo", id="todo-form-title", classes="todo-title")
                yield TodoTitleInput(placeholder="Title", id="todo-title-input")
                yield TextArea(placeholder="Notes (optional)", id="todo-notes-input")
                yield Input(
                    placeholder="Due date: YYYY-MM-DD (optional)",
                    id="todo-due-date-input",
                )
                yield Static(id="todo-form-error", classes="todo-error")
                with Horizontal(classes="todo-actions"):
                    yield Button("Save", id="todo-save", variant="success")
                    yield Button("Cancel", id="todo-form-cancel")

            with Vertical(id="todo-detail", classes="todo-view"):
                yield Label("Todo", classes="todo-title")
                with VerticalScroll(classes="todo-list"):
                    yield Static(id="todo-detail-content")
                with Horizontal(classes="todo-actions"):
                    yield TodoInitialFocusButton("Back", id="todo-detail-back")

            with Vertical(id="todo-delete-confirm", classes="todo-view"):
                yield Label("Delete todo", classes="todo-title")
                yield Static(
                    "This permanently deletes the selected todo.",
                    classes="todo-warning",
                )
                with Horizontal(classes="todo-actions"):
                    yield TodoInitialFocusButton("Cancel", id="todo-delete-cancel")
                    yield Button(
                        "Delete permanently", id="todo-delete", variant="error"
                    )

            with Vertical(id="todo-clear-confirm", classes="todo-view"):
                yield Label("Delete database", classes="todo-title")
                yield Static(
                    "This permanently deletes every todo and cannot be undone.",
                    classes="todo-warning",
                )
                with Horizontal(classes="todo-actions"):
                    yield TodoInitialFocusButton("Cancel", id="todo-clear-cancel")
                    yield Button("Delete database", id="todo-clear", variant="error")

        yield Label("Todo", classes="caption")

    def on_mount(self) -> None:
        """Render the persisted summary without creating a database."""
        self.refresh_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle summary, form, and destructive confirmation buttons."""
        button_id = event.button.id
        if button_id == "todo-manage":
            self.show_view("todo-context")
        elif button_id == "todo-save":
            self.save_todo()
        elif button_id == "todo-form-cancel":
            self.show_view("todo-context")
        elif button_id == "todo-detail-back":
            self.open_selector("browse")
        elif button_id == "todo-delete-cancel":
            self.open_selector("delete")
        elif button_id == "todo-delete":
            self.store.delete_todo(self.selected_todo_id or 0)
            self.refresh_summary()
            self.show_view("todo-context")
        elif button_id == "todo-clear-cancel":
            self.show_view("todo-context")
        elif button_id == "todo-clear":
            self.store.delete_database()
            self.refresh_summary()
            self.close_context()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Route mouse and keyboard selection from the active option list."""
        option_id = event.option_id
        if option_id is None:
            return
        if event.option_list.id == "todo-menu":
            if option_id == "exit":
                self.close_context()
            else:
                self.pending_action = option_id
                self.ensure_database()
        elif event.option_list.id == "todo-create-choice":
            if option_id == "yes":
                self.store.initialise()
                self.continue_action()
            else:
                self.close_context()
        elif event.option_list.id == "todo-selector-list":
            if option_id == "back":
                self.show_view("todo-context")
            elif option_id.startswith("todo-"):
                self.select_todo(int(option_id.removeprefix("todo-")))

    @property
    def store(self) -> TodoStore:
        """Return a short-lived repository for the widget's configured path."""
        return TodoStore(self.database_path)

    def ensure_database(self) -> None:
        """Create only after confirmation, otherwise continue the requested action."""
        if self.store.exists():
            self.continue_action()
        else:
            self.show_view("todo-create-database")

    def continue_action(self) -> None:
        """Resume the action selected before the database-existence check."""
        if self.pending_action == "add":
            self.open_form()
        elif self.pending_action in {"browse", "edit", "delete"}:
            self.open_selector(self.pending_action)
        elif self.pending_action == "clear":
            self.show_view("todo-clear-confirm")

    def open_selector(self, mode: str) -> None:
        """Populate the shared selector for browse, edit, or delete mode."""
        self.selection_mode = mode
        selector = self.query_one("#todo-selector-list", TodoOptionList)
        title = self.query_one("#todo-selector-title", Label)
        title.update(f"{mode.title()} todo")
        todos = self.store.list_todos()
        options = [
            Option(self.todo_option_label(todo), id=f"todo-{todo.id}") for todo in todos
        ]
        if not options:
            options = [Option("No todos available", id="empty", disabled=True)]
        options.append(Option("Back", id="back"))
        selector.set_options(options)
        self.show_view("todo-selector")

    def select_todo(self, todo_id: int) -> None:
        """Open the action appropriate to the selected todo."""
        todo = self.store.get_todo(todo_id)
        if todo is None:
            self.open_selector(self.selection_mode or "browse")
            return
        self.selected_todo_id = todo.id
        if self.selection_mode == "browse":
            self.show_detail(todo)
        elif self.selection_mode == "edit":
            self.open_form(todo)
        elif self.selection_mode == "delete":
            self.show_view("todo-delete-confirm")

    def open_form(self, todo: TodoItem | None = None) -> None:
        """Show the shared add/edit form, optionally populated from a todo."""
        self.selected_todo_id = todo.id if todo is not None else None
        self.query_one("#todo-form-title", Label).update(
            "Edit todo" if todo is not None else "Add todo"
        )
        self.query_one("#todo-title-input", Input).value = todo.title if todo else ""
        self.query_one("#todo-notes-input", TextArea).text = (
            todo.notes or "" if todo else ""
        )
        self.query_one("#todo-due-date-input", Input).value = (
            todo.due_date or "" if todo else ""
        )
        self.query_one("#todo-form-error", Static).update("")
        self.show_view("todo-form")

    def save_todo(self) -> None:
        """Validate and persist the shared add/edit form."""
        title = self.query_one("#todo-title-input", Input).value.strip()
        notes = self.query_one("#todo-notes-input", TextArea).text.strip() or None
        due_date = self.query_one("#todo-due-date-input", Input).value.strip() or None
        error = self.query_one("#todo-form-error", Static)
        if not title:
            error.update("Title is required.")
            return
        if due_date is not None:
            try:
                date.fromisoformat(due_date)
            except ValueError:
                error.update("Due date must use YYYY-MM-DD.")
                return
        if self.selected_todo_id is None:
            self.store.create_todo(title, notes, due_date)
        else:
            self.store.update_todo(self.selected_todo_id, title, notes, due_date)
        self.refresh_summary()
        self.show_view("todo-context")

    def show_detail(self, todo: TodoItem) -> None:
        """Render a selected todo in the read-only browse view."""
        due_date = todo.due_date or "No due date"
        notes = todo.notes or "No notes"
        self.query_one("#todo-detail-content", Static).update(
            f"{todo.title}\n\nDue: {due_date}\n\n{notes}"
        )
        self.show_view("todo-detail")

    def refresh_summary(self) -> None:
        """Refresh the scrollable summary without implicitly creating the database."""
        summary = self.query_one("#todo-summary-list", Static)
        if not self.store.exists():
            summary.update("No todo database yet.\n\nSelect Manage todos to begin.")
            return
        todos = self.store.list_todos()
        if not todos:
            summary.update("No todos yet.")
            return
        summary.update("\n".join(self.todo_option_label(todo) for todo in todos))

    def show_view(self, view_id: str) -> None:
        """Display an in-widget view and keep the active border in sync."""
        views = self.query_one(ContentSwitcher)
        views.current = view_id
        views.get_child_by_id(view_id).display = True
        self.set_class(view_id != "todo-summary", "interacting")

    def close_context(self) -> None:
        """Return to the passive summary and remove the keyboard-focus indicator."""
        self.pending_action = None
        self.selection_mode = None
        self.selected_todo_id = None
        self.refresh_summary()
        self.show_view("todo-summary")

    def action_back(self) -> None:
        """Use Escape as a safe return to the context menu or summary."""
        view_id = self.query_one(ContentSwitcher).current
        if view_id == "todo-context":
            self.close_context()
        elif view_id != "todo-summary":
            self.show_view("todo-context")

    @staticmethod
    def todo_option_label(todo: TodoItem) -> str:
        """Return a concise canonical-order list label for a todo."""
        return f"{todo.id}. {todo.title}" + (
            f" — due {todo.due_date}" if todo.due_date else ""
        )


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
