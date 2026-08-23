import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Label, Static

from modules.composer import compose_from_config
from modules.conf import Config
from modules.custom import Custom
from modules.elements import Clock, Stopwatch, SystemMonitor, Timer
from modules.todo import Todo
from modules.weather import Weather


class CustomApp(App):
    def compose(self) -> ComposeResult:
        custom = Custom()
        custom.text = "Focus time"
        custom.clock = True
        custom.timezone = "UTC"
        custom.timer = True
        custom.stopwatch = True
        custom.system_monitor = True
        custom.todo = True
        custom.weather = True
        yield custom


class EmptyCustomApp(App):
    def compose(self) -> ComposeResult:
        yield Custom()


class TestCustom:
    def test_renders_enabled_elements_in_fixed_vertical_order(self):
        async def run_test() -> None:
            async with CustomApp().run_test(size=(100, 50)) as pilot:
                custom = pilot.app.query_one(Custom)
                children = list(custom.children)

                assert isinstance(children[0], Label)
                assert str(children[0].render()) == "Focus time"
                assert [type(child) for child in children[1:]] == [
                    Clock,
                    Timer,
                    Stopwatch,
                    SystemMonitor,
                    Todo,
                    Weather,
                ]
                assert custom.query_one(Clock).timezone == "UTC"
                assert all(child.has_class("custom-element") for child in children[1:])

        asyncio.run(run_test())

    def test_shows_an_empty_state_without_enabled_elements(self):
        async def run_test() -> None:
            async with EmptyCustomApp().run_test() as pilot:
                empty_state = pilot.app.query_one(".custom-empty", Static)

                assert str(empty_state.render()) == "No custom elements enabled"

        asyncio.run(run_test())

    def test_composer_applies_custom_options(self):
        custom = compose_from_config(
            Config.model_validate(
                {
                    "kind": "Custom",
                    "opts": {
                        "text": "Work",
                        "clock": True,
                        "timezone": "UTC",
                        "weather": True,
                    },
                }
            )
        )

        assert isinstance(custom, Custom)
        assert custom.text == "Work"
        assert custom.clock
        assert custom.timezone == "UTC"
        assert custom.weather

    def test_horizontal_layout_option_is_rejected(self):
        custom = compose_from_config(
            Config.model_validate({"kind": "Custom", "opts": {"layout": "horizontal"}})
        )

        assert custom is None
