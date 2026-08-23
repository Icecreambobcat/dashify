from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from modules.composer import compose_from_config
from modules.conf import make_config


class Dashify(App):
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", key_display="^q")]

    DEFAULT_CSS = """
    #config-warning-screen {
        width: 1fr;
        height: 1fr;
        align: center middle;
    }

    #config-warning {
        width: 50;
        height: 5;
        border: round $warning;
        padding: 1;
        color: $warning;
        content-align: center middle;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        config = make_config()
        if config is not None and (layout := compose_from_config(config)) is not None:
            yield layout
        else:
            with Container(id="config-warning-screen"):
                yield Static(
                    "Configuration could not be loaded.\n"
                    "Check dashify.toml and restart.",
                    id="config-warning",
                )
        yield Footer()
