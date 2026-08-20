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
    )
]


@pytest.mark.parametrize(["config", "expected"], values)
def test_flatten_config(config, expected):
    assert flatten_config(config) == expected
