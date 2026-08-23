import asyncio

from textual.containers import Container
from textual.widgets import Static

from modules import app
from modules.conf import Config
from modules.elements import HBox, InvalidConfig


class TestDashify:
    def test_shows_a_centred_warning_for_malformed_config(self, monkeypatch):
        monkeypatch.setattr(app, "make_config", lambda: None)

        async def run_test() -> None:
            async with app.Dashify().run_test(size=(100, 30)) as pilot:
                warning_screen = pilot.app.query_one(
                    "#config-warning-screen", Container
                )
                warning = pilot.app.query_one("#config-warning", Static)

                assert warning.region.width == 50
                assert warning.region.x == warning_screen.region.x + 25
                assert "Configuration could not be loaded." in str(warning.render())
                assert "Check dashify.toml and restart." in str(warning.render())

        asyncio.run(run_test())

    def test_shows_a_warning_for_an_unsupported_root_widget(self, monkeypatch):
        monkeypatch.setattr(app, "make_config", lambda: object())
        monkeypatch.setattr(app, "compose_from_config", lambda config: None)

        async def run_test() -> None:
            async with app.Dashify().run_test() as pilot:
                assert len(pilot.app.query("#config-warning")) == 1

        asyncio.run(run_test())

    def test_shows_a_warning_in_place_of_an_invalid_child(self, monkeypatch):
        monkeypatch.setattr(
            app,
            "make_config",
            lambda: Config.model_validate(
                {
                    "kind": "HBox",
                    "children": [
                        {"kind": "Clock"},
                        {"kind": "Clock", "opts": {"timezone": 10}},
                    ],
                }
            ),
        )

        async def run_test() -> None:
            async with app.Dashify().run_test(size=(100, 30)) as pilot:
                layout = pilot.app.query_one(HBox)
                warning = pilot.app.query_one(InvalidConfig)

                assert len(pilot.app.query("#config-warning")) == 0
                assert warning.region.width == layout.region.width // 2
                assert warning.region.x == layout.region.x + layout.region.width // 2

        asyncio.run(run_test())
