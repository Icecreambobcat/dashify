from pathlib import Path
import sys
from tomlkit.toml_file import TOMLFile


def get_config_path() -> Path:
    """
    Returns a path to a valid configuration file.
    """
    USER_HOME = Path.home()
    CONFIG_FILE = USER_HOME / ".config" / "dashify" / "dashify.toml"
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    # Exists in unix-style config home?
    if CONFIG_FILE.is_file():
        return CONFIG_FILE

    # Pyinstaller distribution?
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "defaults" / "dashify.toml"

    # Fallback to default
    return PROJECT_ROOT / "defaults" / "dashify.toml"


def get_config_dict(path: Path) -> dict:
    """
    Convert toml file at path to a pure python object
    """
    file = TOMLFile(path).read()
    return file.unwrap()
