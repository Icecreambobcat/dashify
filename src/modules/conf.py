from pydantic import BaseModel
from modules.parser import get_config_path, get_config_dict


class Config(BaseModel):
    """
    Uses a pydantic model to ensure valid configs.

    Provides recursive checking to validate a widget-tree config.
    """

    kind: str
    opts: dict[str, str] | None
    children: list[Config] | None


def flatten_config(config: dict) -> dict:
    """
    Recursively flattens the intuitive toml layout.

    This is easier for pydantic to handle as well as for the app to process.
    """
    if set(config.keys()) | {"kind", "opts"} == {"kind", "opts"}:
        return config

    children = []

    for key, value in config.items():
        if isinstance(value, dict) and key != "opts":
            children.append(flatten_config(value))

    if "opts" in config.keys():
        return {"kind": config["kind"], "opts": config["opts"], "children": children}

    return {"kind": config["kind"], "children": children}


def make_config() -> Config:
    """
    Validation and generating a reference in 1 step
    """
    return Config(**flatten_config(get_config_dict(get_config_path())))
