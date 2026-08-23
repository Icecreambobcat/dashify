"""SQLite persistence for Dashify's Todo widget."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3

DEFAULT_TODO_DATABASE_PATH = Path.home() / ".local" / "state" / "dashify" / "todo.db"


@dataclass(frozen=True)
class TodoItem:
    """A persisted todo entry in canonical insertion order."""

    id: int
    title: str
    notes: str | None
    due_date: str | None
    created_at: str
    updated_at: str


class TodoStore:
    """Perform SQLite operations without creating a database implicitly."""

    def __init__(self, path: Path = DEFAULT_TODO_DATABASE_PATH) -> None:
        self.path = path

    def exists(self) -> bool:
        """Return whether the configured SQLite database already exists."""
        return self.path.is_file()

    def initialise(self) -> None:
        """Create the database and its initial schema after user confirmation."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect(create=True) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                    notes TEXT,
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)

    def list_todos(self) -> list[TodoItem]:
        """Return all todos in their canonical first-come-first-served order."""
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT id, title, notes, due_date, created_at, updated_at
                FROM todos
                ORDER BY id ASC
                """).fetchall()
        return [TodoItem(**dict(row)) for row in rows]

    def get_todo(self, todo_id: int) -> TodoItem | None:
        """Return a todo by ID, or ``None`` when it no longer exists."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, notes, due_date, created_at, updated_at
                FROM todos
                WHERE id = ?
                """,
                (todo_id,),
            ).fetchone()
        return TodoItem(**dict(row)) if row is not None else None

    def create_todo(self, title: str, notes: str | None, due_date: str | None) -> int:
        """Insert a todo and return its canonical database ID."""
        timestamp = self._timestamp()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO todos (title, notes, due_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, notes, due_date, timestamp, timestamp),
            )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return the inserted todo ID")
        return cursor.lastrowid

    def update_todo(
        self, todo_id: int, title: str, notes: str | None, due_date: str | None
    ) -> None:
        """Update an existing todo without changing its canonical order."""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE todos
                SET title = ?, notes = ?, due_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, notes, due_date, self._timestamp(), todo_id),
            )

    def delete_todo(self, todo_id: int) -> None:
        """Permanently delete a todo."""
        with self._connect() as connection:
            connection.execute("DELETE FROM todos WHERE id = ?", (todo_id,))

    def delete_database(self) -> None:
        """Permanently remove the database and any SQLite WAL sidecar files."""
        for path in (
            self.path,
            self.path.with_name(f"{self.path.name}-wal"),
            self.path.with_name(f"{self.path.name}-shm"),
        ):
            if path.exists():
                path.unlink()

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        """Open an existing or explicitly initialised database connection."""
        if not create and not self.exists():
            raise FileNotFoundError(self.path)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _timestamp() -> str:
        """Return a timezone-aware UTC timestamp suitable for SQLite storage."""
        return datetime.now(UTC).isoformat()
