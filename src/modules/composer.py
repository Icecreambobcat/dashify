from textual.widget import Widget

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

WIDGET_OPTIONS: dict[type[Widget], set[str]] = {Clock: {"timezone"}}


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
    if isinstance(element, (HBox, VBox)):
        element.elements = [
            child
            for config_child in conf.children or []
            if (child := compose_from_config(config_child, is_child=True)) is not None
        ]
        return element

    for option, value in (conf.opts or {}).items():
        if option in WIDGET_OPTIONS.get(element_type, set()) and isinstance(value, str):
            setattr(element, option, value)
    return element
