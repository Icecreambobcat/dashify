from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.parser import get_config_dict, get_config_path

META_CONTAINER_KINDS = {"hbox", "vbox"}
INVALID_CONFIG_KIND = "__invalid__"


def invalid_config(message: str) -> dict[str, Any]:
    """Return a normalised configuration node that composes to a warning."""
    return {"kind": INVALID_CONFIG_KIND, "opts": {"message": message}}


class Config(BaseModel):
    """A validated widget-tree node with optional configuration and children."""

    model_config = ConfigDict(extra="ignore")
    kind: str
    opts: dict[str, Any] | None = None
    children: list[Config] | None = None


def flatten_config(config: object) -> dict[str, Any] | None:
    """Normalise a TOML widget table, ignoring malformed nodes safely.

    Only ``HBox`` and ``VBox`` treat named nested tables as child widgets.
    Named tables on all other widget kinds are ignored. Invalid ``opts`` values
    and child tables without a usable ``kind`` become in-layout warnings.
    """
    if not isinstance(config, dict):
        return None

    kind = config.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        return None

    flattened: dict[str, Any] = {"kind": kind}
    opts = config.get("opts")
    if isinstance(opts, dict):
        flattened["opts"] = opts
    elif opts is not None:
        return invalid_config("Malformed opts table")

    if kind.casefold() in META_CONTAINER_KINDS:
        children = []
        for key, value in config.items():
            if key in {"kind", "opts"} or not isinstance(value, dict):
                continue
            child = flatten_config(value)
            children.append(child or invalid_config("Invalid widget configuration"))
        flattened["children"] = children

    return flattened


def make_config() -> Config | None:
    """Load a valid dashboard configuration, returning ``None`` for bad input."""
    document = get_config_dict(get_config_path())
    flattened = flatten_config(document.get("widgets", document))
    return Config.model_validate(flattened) if flattened is not None else None
