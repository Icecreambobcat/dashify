from modules.composer import compose_from_config
from modules.conf import Config, make_config
from modules.elements import Clock, HBox, InvalidConfig, Timer, VBox


def test_composes_supported_nested_layout_and_allowed_options():
    config = Config.model_validate(
        {
            "kind": "HBox",
            "children": [
                {
                    "kind": "VBox",
                    "children": [
                        {"kind": "Clock", "opts": {"timezone": "UTC"}},
                        {"kind": "Timer"},
                    ],
                }
            ],
        }
    )

    layout = compose_from_config(config)

    assert isinstance(layout, HBox)
    assert len(layout.elements) == 1
    column = layout.elements[0]
    assert isinstance(column, VBox)
    assert len(column.elements) == 2
    assert isinstance(column.elements[0], Clock)
    assert column.elements[0].timezone == "UTC"
    assert isinstance(column.elements[1], Timer)


def test_shows_warnings_for_unknown_widgets_and_invalid_options():
    config = Config.model_validate(
        {
            "kind": "VBox",
            "children": [
                {"kind": "Unknown"},
                {"kind": "Clock", "opts": {"timezone": 10}},
                {"kind": "Clock", "opts": {"not_an_option": "value"}},
                {"kind": "Timer", "opts": {"mode": "running"}},
            ],
        }
    )

    layout = compose_from_config(config)

    assert isinstance(layout, VBox)
    assert len(layout.elements) == 4
    assert isinstance(layout.elements[0], InvalidConfig)
    assert isinstance(layout.elements[1], InvalidConfig)
    assert isinstance(layout.elements[2], InvalidConfig)
    timer = layout.elements[3]
    assert isinstance(timer, Timer)
    assert timer.mode == "running"


def test_ignores_an_unknown_root_widget():
    assert compose_from_config(Config.model_validate({"kind": "Unknown"})) is None


def test_shows_a_root_warning_for_invalid_root_options():
    config = Config.model_validate({"kind": "Clock", "opts": {"timezone": 10}})

    assert compose_from_config(config) is None


def test_shows_a_warning_for_a_malformed_child_config():
    config = Config.model_validate(
        {
            "kind": "HBox",
            "children": [
                {"kind": "Clock"},
                {
                    "kind": "__invalid__",
                    "opts": {"message": "Invalid widget configuration"},
                },
            ],
        }
    )

    layout = compose_from_config(config)

    assert isinstance(layout, HBox)
    assert isinstance(layout.elements[0], Clock)
    warning = layout.elements[1]
    assert isinstance(warning, InvalidConfig)
    assert "Invalid widget configuration" in str(warning.render())


def test_default_clock_timezone_is_supplied_by_the_app():
    config = make_config()

    assert config is not None
    layout = compose_from_config(config)
    assert isinstance(layout, HBox)
    right_column = layout.elements[1]
    assert isinstance(right_column, VBox)
    top_row = right_column.elements[0]
    assert isinstance(top_row, HBox)
    clock = top_row.elements[0]
    assert isinstance(clock, Clock)
    assert clock.timezone == "local"
