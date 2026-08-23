from pathlib import Path
import sys
from typing import Any

from tomlkit.toml_file import TOMLFile


def _default_config_path(module_path: Path | None = None) -> Path:
    """Locate defaults in either a source checkout or an installed wheel."""
    module_path = (module_path or Path(__file__)).resolve()
    candidates = (
        module_path.parents[1] / "defaults" / "dashify.toml",
        module_path.parents[2] / "defaults" / "dashify.toml",
    )
    return next((path for path in candidates if path.is_file()), candidates[-1])


def get_config_path() -> Path:
    """Return the user, packaged, or project-default configuration path."""
    config_file = Path.home() / ".config" / "dashify" / "dashify.toml"

    if config_file.is_file():
        return config_file

    if getattr(sys, "frozen", False):
        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root is not None:
            return Path(frozen_root) / "defaults" / "dashify.toml"

    return _default_config_path()


def get_config_dict(path: Path) -> dict[str, Any]:
    """Convert a TOML file to a pure Python object, ignoring unreadable input."""
    try:
        return TOMLFile(path).read().unwrap()
    except Exception:
        return {}
