from pathlib import Path
import sys
import tomlkit


def get_config_path() -> Path:
    USER_HOME = Path.home()
    CONFIG_FILE = USER_HOME / ".config" / "dashify" / "dashify.toml"
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    if CONFIG_FILE.is_file():
        return CONFIG_FILE
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "defaults" / "dashify.toml"
    return PROJECT_ROOT / "defaults" / "dashify.toml"


def get_config() -> dict: ...
