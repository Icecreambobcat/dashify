import pytest

from modules.conf import flatten_config

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
        {"kind": "Box", "children": [{"kind": "Label", "opts": {"text": "hi"}}]},
    ),
    (
        {"kind": "A", "B": {"kind": "C", "D": {"kind": "E"}}},
        {"kind": "A", "children": [{"kind": "C", "children": [{"kind": "E"}]}]},
    ),
    ({"kind": "Static", "opts": None}, {"kind": "Static", "opts": None}),
]


@pytest.mark.parametrize(["config", "expected"], values)
def test_flatten_config(config, expected):
    assert flatten_config(config) == expected
