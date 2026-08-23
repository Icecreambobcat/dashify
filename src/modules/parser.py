from pathlib import Path
import sys
from tomlkit.toml_file import TOMLFile


def get_config_path() -> Path:
    """Return the user, packaged, or project-default configuration path."""
    config_file = Path.home() / ".config" / "dashify" / "dashify.toml"
    project_root = Path(__file__).resolve().parents[2]

    if config_file.is_file():
        return config_file

    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "defaults" / "dashify.toml"

    return project_root / "defaults" / "dashify.toml"


def get_config_dict(path: Path) -> dict:
    """Convert a TOML file to a pure Python object, ignoring unreadable input."""
    try:
        return TOMLFile(path).read().unwrap()
    except Exception:
        return {}
