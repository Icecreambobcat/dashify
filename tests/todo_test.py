import asyncio
from pathlib import Path
import sqlite3

import pytest
from textual.app import App, ComposeResult
from textual.widgets import ContentSwitcher, Input, Label, Static, TextArea

from modules.todo import Todo
from modules.todo_store import TodoStore


class TodoApp(App):
    database_path: Path

    def compose(self) -> ComposeResult:
        todo = Todo()
        todo.database_path = self.database_path
        yield todo


class TestTodoStore:
    def test_reading_a_missing_database_does_not_create_it(self, tmp_path: Path):
        store = TodoStore(tmp_path / "todo.db")

        with pytest.raises(FileNotFoundError):
            store.list_todos()

        assert not store.exists()
        store.delete_database()
        assert not store.exists()

    def test_persists_todos_in_canonical_order(self, tmp_path: Path):
        store = TodoStore(tmp_path / "todo.db")

        assert not store.exists()
        store.initialise()
        first_id = store.create_todo("First", None, None)
        second_id = store.create_todo("Second", "Notes", "2026-08-24")

        assert [todo.id for todo in store.list_todos()] == [first_id, second_id]

        store.update_todo(first_id, "Updated", "Edited notes", "2026-08-25")
        updated_todo = store.get_todo(first_id)
        assert updated_todo is not None
        assert updated_todo.title == "Updated"

        store.delete_todo(second_id)
        assert [todo.id for todo in store.list_todos()] == [first_id]

        store.delete_database()
        assert not store.exists()

    def test_database_rejects_blank_titles(self, tmp_path: Path):
        store = TodoStore(tmp_path / "todo.db")
        store.initialise()

        with pytest.raises(sqlite3.IntegrityError):
            store.create_todo("   ", None, None)


class TestTodo:
    def test_displays_title_in_summary_heading(self, tmp_path: Path):
        async def run_test() -> None:
            app = TodoApp()
            app.database_path = tmp_path / "todo.db"
            async with app.run_test():
                title = app.query_one("#todo-widget-title", Label)

                assert str(title.render()) == "Todos"

        asyncio.run(run_test())

    def test_database_gate_add_delete_and_clear_flow(self, tmp_path: Path):
        async def run_test() -> None:
            app = TodoApp()
            app.database_path = tmp_path / "todo.db"
            async with app.run_test() as pilot:
                todo = pilot.app.query_one(Todo)
                views = todo.query_one(ContentSwitcher)

                await pilot.click("#todo-manage")
                assert views.current == "todo-context"
                assert todo.has_class("interacting")
                assert todo.query_one("#todo-menu").has_focus

                await pilot.press("down", "enter")
                assert views.current == "todo-create-database"

                await pilot.press("enter")
                assert views.current == "todo-form"
                assert todo.store.exists()
                assert todo.query_one("#todo-title-input", Input).has_focus

                todo.query_one("#todo-title-input", Input).value = "Buy milk"
                todo.query_one("#todo-notes-input", TextArea).text = "Semi-skimmed"
                todo.query_one("#todo-due-date-input", Input).value = "2026-08-24"
                todo.save_todo()

                assert [item.title for item in todo.store.list_todos()] == ["Buy milk"]
                assert views.current == "todo-context"

                todo.open_form()
                todo.save_todo()
                assert (
                    str(todo.query_one("#todo-form-error", Static).render())
                    == "Title is required."
                )
                assert [item.title for item in todo.store.list_todos()] == ["Buy milk"]

                todo.query_one("#todo-title-input", Input).value = "Pay rent"
                todo.query_one("#todo-due-date-input", Input).value = "24-08-2026"
                todo.save_todo()
                assert (
                    str(todo.query_one("#todo-form-error", Static).render())
                    == "Due date must use YYYY-MM-DD."
                )
                assert [item.title for item in todo.store.list_todos()] == ["Buy milk"]

                todo.open_selector("delete")
                todo.select_todo(1)
                assert views.current == "todo-delete-confirm"
                await pilot.pause()
                await pilot.click("#todo-delete")
                assert todo.store.list_todos() == []

                todo.pending_action = "clear"
                todo.continue_action()
                assert views.current == "todo-clear-confirm"
                await pilot.pause()
                await pilot.click("#todo-clear")
                assert not todo.store.exists()
                assert views.current == "todo-summary"
                assert not todo.has_class("interacting")

        asyncio.run(run_test())
