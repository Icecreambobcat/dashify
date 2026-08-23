"""Interactive Todo widget built on Dashify's shared element primitives."""

from datetime import date
from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalGroup, VerticalScroll
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    OptionList,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

from modules.elements import WIDGET_FRAME_CSS
from modules.todo_store import DEFAULT_TODO_DATABASE_PATH, TodoItem, TodoStore


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
    Todo .todo-view {{ width: 1fr; height: 1fr; }}
    Todo .todo-view {{ padding: 1; }}
    Todo .todo-list, Todo .todo-menu, Todo .todo-selector {{ height: 1fr; }}
    Todo .todo-list {{ border: tall $border; padding: 0 1; }}
    Todo .todo-actions {{ height: auto; margin: 1 0 0 0; }}
    Todo .todo-actions Button {{ width: 1fr; }}
    Todo .todo-title {{ text-style: bold; text-align: center; margin: 0 0 1 0; }}
    Todo .todo-message, Todo .todo-error, Todo .todo-key-hint {{ text-align: center; }}
    Todo .todo-key-hint {{ color: $text-muted; height: 1; margin: 1 0 0 0; }}
    Todo .todo-error {{ color: $error; height: 1; }}
    Todo .todo-warning {{ color: $warning; text-style: bold; text-align: center; border: round $warning; padding: 1; margin: 1 0; }}
    Todo TextArea {{ height: 6; margin: 1 0; }}
    Todo .caption {{ width: 1fr; height: 1; text-align: center; color: $text-muted; text-style: bold; margin: 1 0 0 0; }}
    """

    def compose(self) -> ComposeResult:
        """Compose the summary and every full-widget interaction view."""
        with ContentSwitcher(initial="todo-summary", id="todo-views"):
            with Vertical(id="todo-summary", classes="todo-view"):
                yield Label("Todos", id="todo-widget-title", classes="todo-title")
                with VerticalScroll(classes="todo-list"):
                    yield Static(id="todo-summary-list", markup=False)
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
                    yield Static(id="todo-detail-content", markup=False)
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
                yield Label("Delete todo database", classes="todo-title")
                yield Static(
                    "This permanently deletes every todo and cannot be undone.",
                    classes="todo-warning",
                )
                with Horizontal(classes="todo-actions"):
                    yield TodoInitialFocusButton("Cancel", id="todo-clear-cancel")
                    yield Button("Delete database", id="todo-clear", variant="error")
        yield Label("Todo", classes="caption")

    def on_mount(self) -> None:
        """Render the persisted summary when the widget first mounts."""
        self.refresh_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch buttons in the currently visible Todo view."""
        button_id = event.button.id
        if button_id is None:
            return
        actions = {
            "todo-manage": lambda: self.show_view("todo-context"),
            "todo-save": self.save_todo,
            "todo-form-cancel": lambda: self.show_view("todo-context"),
            "todo-detail-back": lambda: self.open_selector("browse"),
            "todo-delete-cancel": lambda: self.open_selector("delete"),
            "todo-clear-cancel": lambda: self.show_view("todo-context"),
        }
        if button_id == "todo-delete":
            self.store.delete_todo(self.selected_todo_id or 0)
            self.refresh_summary()
            self.show_view("todo-context")
        elif button_id == "todo-clear":
            self.store.delete_database()
            self.refresh_summary()
            self.close_context()
        elif action := actions.get(button_id):
            action()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Continue the menu or selection action chosen by the user."""
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
        """Return a short-lived store for the configured database path."""
        return TodoStore(self.database_path)

    def ensure_database(self) -> None:
        """Continue an action or ask permission to create its database."""
        if self.store.exists():
            self.continue_action()
        else:
            self.show_view("todo-create-database")

    def continue_action(self) -> None:
        """Open the view associated with the pending context-menu action."""
        if self.pending_action == "add":
            self.open_form()
        elif self.pending_action in {"browse", "edit", "delete"}:
            self.open_selector(self.pending_action)
        elif self.pending_action == "clear":
            self.show_view("todo-clear-confirm")

    def open_selector(self, mode: str) -> None:
        """Show canonically ordered todos for browsing, editing, or deletion."""
        self.selection_mode = mode
        self.query_one("#todo-selector-title", Label).update(f"{mode.title()} todo")
        todos = self.store.list_todos()
        options = [
            Option(Text(self.todo_option_label(todo)), id=f"todo-{todo.id}")
            for todo in todos
        ]
        if not options:
            options = [Option("No todos available", id="empty", disabled=True)]
        self.query_one("#todo-selector-list", TodoOptionList).set_options(
            [*options, Option("Back", id="back")]
        )
        self.show_view("todo-selector")

    def select_todo(self, todo_id: int) -> None:
        """Open the selected todo in the view required by the current mode."""
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
        """Open the shared form for a new or existing todo."""
        self.selected_todo_id = todo.id if todo else None
        self.query_one("#todo-form-title", Label).update(
            "Edit todo" if todo else "Add todo"
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
        """Validate and persist values from the add/edit form."""
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
        """Display all fields for a selected todo."""
        self.query_one("#todo-detail-content", Static).update(
            f"{todo.title}\n\nDue: {todo.due_date or 'No due date'}\n\n{todo.notes or 'No notes'}"
        )
        self.show_view("todo-detail")

    def refresh_summary(self) -> None:
        """Refresh the non-interactive, scrollable todo summary."""
        summary = self.query_one("#todo-summary-list", Static)
        if not self.store.exists():
            summary.update("No todo database yet.\n\nSelect Manage todos to begin.")
            return
        todos = self.store.list_todos()
        summary.update(
            "\n".join(self.todo_option_label(todo) for todo in todos)
            if todos
            else "No todos yet."
        )

    def show_view(self, view_id: str) -> None:
        """Switch views and indicate whether keyboard input is captured."""
        views = self.query_one(ContentSwitcher)
        views.current = view_id
        views.get_child_by_id(view_id).display = True
        self.set_class(view_id != "todo-summary", "interacting")

    def close_context(self) -> None:
        """Clear interaction state and return to the summary."""
        self.pending_action = self.selection_mode = None
        self.selected_todo_id = None
        self.refresh_summary()
        self.show_view("todo-summary")

    def action_back(self) -> None:
        """Move towards the summary when Escape is pressed."""
        if self.query_one(ContentSwitcher).current == "todo-context":
            self.close_context()
        elif self.query_one(ContentSwitcher).current != "todo-summary":
            self.show_view("todo-context")

    @staticmethod
    def todo_option_label(todo: TodoItem) -> str:
        """Format a todo for summary and selector views."""
        return f"{todo.id}. {todo.title}" + (
            f" — due {todo.due_date}" if todo.due_date else ""
        )
