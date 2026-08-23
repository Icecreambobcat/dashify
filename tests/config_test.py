from typing import Any

import pytest

from modules.conf import Config, flatten_config, make_config

values = [
    (
        {
            "kind": "Vbox",
            "top": {
                "kind": "Hbox",
                "left": {"kind": "Static", "opts": {"text": "left"}},
                "right": {"kind": "Static"},
            },
            "bottom": {"kind": "Static"},
        },
        {
            "kind": "Vbox",
            "children": [
                {
                    "kind": "Hbox",
                    "children": [
                        {"kind": "Static", "opts": {"text": "left"}},
                        {"kind": "Static"},
                    ],
                },
                {
                    "kind": "Static",
                },
            ],
        },
    ),
    (
        {"kind": "Button", "opts": {"label": "Click me"}},
        {"kind": "Button", "opts": {"label": "Click me"}},
    ),
    (
        {"kind": "Box", "content": {"kind": "Label", "opts": {"text": "hi"}}},
        {"kind": "Box"},
    ),
    (
        {"kind": "A", "B": {"kind": "C", "D": {"kind": "E"}}},
        {"kind": "A"},
    ),
    ({"kind": "Static", "opts": None}, {"kind": "Static"}),
]


@pytest.mark.parametrize(["config", "expected"], values)
def test_flatten_config(config: dict[str, Any], expected: dict[str, Any]):
    assert flatten_config(config) == expected


@pytest.mark.parametrize(
    "config",
    [None, [], {}, {"kind": ""}, {"kind": 1}, {"opts": {"timezone": "UTC"}}],
)
def test_flatten_config_ignores_invalid_nodes(config: object):
    assert flatten_config(config) is None


def test_flatten_config_ignores_bad_options_and_children():
    config = {
        "kind": "VBox",
        "valid": {"kind": "Clock"},
        "malformed_opts": {"kind": "Clock", "opts": "not a table"},
        "missing_kind": {"opts": {"timezone": "UTC"}},
        "not_a_table": "ignored",
    }

    assert flatten_config(config) == {
        "kind": "VBox",
        "children": [
            {"kind": "Clock"},
            {
                "kind": "__invalid__",
                "opts": {"message": "Malformed opts table"},
            },
            {
                "kind": "__invalid__",
                "opts": {"message": "Invalid widget configuration"},
            },
        ],
    }


def test_config_allows_missing_optional_fields():
    config = Config.model_validate({"kind": "Todo"})

    assert config.opts is None
    assert config.children is None


def test_default_configuration_validates():
    config = make_config()

    assert config is not None
    assert config.kind == "Hbox"
