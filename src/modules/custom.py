"""Vertical-only custom arrangements composed from Dashify's builtin widgets."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static

from modules.elements import Clock, Stopwatch, SystemMonitor, Timer
from modules.todo import Todo


class Custom(Vertical):
    """A vertical arrangement of builtin widgets selected through ``opts``."""

    text = ""
    clock = False
    timer = False
    stopwatch = False
    system_monitor = False
    todo = False
    timezone = "local"

    DEFAULT_CSS = """
    Custom {
        width: 1fr;
        height: 1fr;
    }

    Custom .custom-element {
        width: 1fr;
        height: 1fr;
        margin: 0;
    }

    Custom .custom-text {
        width: 1fr;
        height: 1;
        text-align: center;
        color: $text-muted;
    }

    Custom .custom-empty {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        text-align: center;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the enabled builtin widgets in their fixed vertical order."""
        if self.text:
            yield Label(self.text, classes="custom-text")

        elements = self.enabled_elements()
        if not elements:
            yield Static("No custom elements enabled", classes="custom-empty")
            return

        for element in elements:
            element.add_class("custom-element")
            yield element

    def enabled_elements(
        self,
    ) -> list[Clock | Timer | Stopwatch | SystemMonitor | Todo]:
        """Return enabled widgets in the documented fixed display order."""
        elements: list[Clock | Timer | Stopwatch | SystemMonitor | Todo] = []
        if self.clock:
            clock = Clock()
            clock.timezone = self.timezone
            elements.append(clock)
        if self.timer:
            elements.append(Timer())
        if self.stopwatch:
            elements.append(Stopwatch())
        if self.system_monitor:
            elements.append(SystemMonitor())
        if self.todo:
            elements.append(Todo())
        return elements
