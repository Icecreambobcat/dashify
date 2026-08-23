from textual.widget import Widget

from typing import Any

from modules.conf import Config, INVALID_CONFIG_KIND
from modules.elements import (
    Clock,
    HBox,
    InvalidConfig,
    Spotify,
    Stopwatch,
    SystemMonitor,
    Timer,
    Todo,
    VBox,
)

ELEMENT_TYPES: dict[str, type[Widget]] = {
    "clock": Clock,
    "hbox": HBox,
    "spotify": Spotify,
    "stopwatch": Stopwatch,
    "systemmonitor": SystemMonitor,
    "timer": Timer,
    "todo": Todo,
    "vbox": VBox,
}


def compose_from_config(conf: Config, *, is_child: bool = False) -> Widget | None:
    """Compose a widget tree, showing warnings in place of invalid child nodes."""
    if conf.kind == INVALID_CONFIG_KIND:
        if not is_child:
            return None
        return InvalidConfig((conf.opts or {}).get("message", "Invalid configuration"))

    element_type = ELEMENT_TYPES.get(conf.kind.casefold())
    if element_type is None:
        return InvalidConfig(f"Unsupported widget: {conf.kind}") if is_child else None

    element = element_type()
    if error := apply_options(element, conf.opts):
        return InvalidConfig(error) if is_child else None

    if isinstance(element, (HBox, VBox)):
        element.elements = [
            child
            for config_child in conf.children or []
            if (child := compose_from_config(config_child, is_child=True)) is not None
        ]
        return element
    return element


def apply_options(element: Widget, options: dict[str, Any] | None) -> str | None:
    """Apply valid TOML options to public widget attributes.

    The current attribute value supplies the expected type. Private, callable,
    unknown, and incompatible attributes are rejected so a configuration error
    remains visible rather than silently changing widget behaviour.
    """
    for name, value in (options or {}).items():
        if name.startswith("_") or not hasattr(element, name):
            return f"Invalid option: {name}"

        current_value = getattr(element, name)
        if callable(current_value) or (
            current_value is not None and type(value) is not type(current_value)
        ):
            return f"Invalid option: {name}"

        try:
            setattr(element, name, value)
        except AttributeError, TypeError, ValueError:
            return f"Invalid option: {name}"
    return None
