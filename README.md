# Dashify

Dashify is a configurable terminal dashboard built with
[Textual](https://textual.textualize.io/). It arranges clocks, timers, todos,
weather, and system information into nested horizontal and vertical tiles.

## Requirements

- Python 3.14 or 3.15
- A terminal with mouse support and Unicode glyphs
- Internet access for the Weather widget

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then
install Dashify as an isolated command-line tool. uv will obtain a compatible
Python interpreter when one is not already available:

```console
uv tool install --python 3.14 dashify
dashify
```

If `dashify` is not found after installation, add uv's executable directory to
your shell path and restart the shell:

```console
uv tool update-shell
```

To install directly from a source checkout instead:

```console
git clone https://github.com/Icecreambobcat/dashify.git
cd dashify
uv tool install --python 3.14 .
```

Upgrade or remove Dashify with:

```console
uv tool upgrade dashify
uv tool uninstall dashify
```

Dashify loads `~/.config/dashify/dashify.toml` when that file exists. Otherwise,
it uses its packaged default configuration. From a source checkout, copy the
documented default before customising your dashboard:

```console
mkdir -p ~/.config/dashify
cp defaults/dashify.toml ~/.config/dashify/dashify.toml
```

Users who installed from PyPI can download the same versioned default:

```console
mkdir -p ~/.config/dashify
curl -L https://raw.githubusercontent.com/Icecreambobcat/dashify/v0.1.2/defaults/dashify.toml \
  -o ~/.config/dashify/dashify.toml
```

Press <kbd>Ctrl</kbd>+<kbd>Q</kbd> to quit.

## Configuration

The dashboard is a tree rooted at the `[widgets]` table. Every widget table
requires a `kind`. `HBox` divides its space equally from left to right, while
`VBox` divides its space equally from top to bottom. Any other nested table name
is simply a readable identifier for a child.

```toml
[widgets]
kind = "HBox"

[widgets.left]
kind = "VBox"

[widgets.left.clock]
kind = "Clock"
opts = { timezone = "Australia/Sydney" }

[widgets.left.timer]
kind = "Timer"

[widgets.right]
kind = "VBox"

[widgets.right.weather]
kind = "Weather"
opts = { location = "Melbourne", units = "metric", refresh_minutes = 15 }

[widgets.right.todos]
kind = "Todo"
```

Only `HBox` and `VBox` treat named nested tables as children. Child tables on
ordinary widgets are ignored. The optional `opts` value must be a TOML table;
inline tables are preferred because they visually distinguish widget options
from layout children.

Malformed roots produce a centred warning screen. An invalid child or invalid
`opts` value produces a warning in that child's tile so that the rest of the
dashboard remains usable.

The widget snippets below are child tables intended to be added beneath an
`HBox` or `VBox` root such as the one in the complete example above.

## Built-in widgets

### Clock

`Clock` displays a 24-hour clock. It uses the local timezone by default.
`timezone` accepts `local`, `UTC`, a UTC offset, or an IANA timezone name.

```toml
[widgets.clock]
kind = "Clock"
opts = { timezone = "Europe/London" }
```

### Timer

`Timer` is a countdown with one Start/Stop/Reset button. While stopped, click
the digits, enter up to six digits in `HHMMSS` order, and press Enter. Input is
right-aligned, so `130` becomes `00:01:30`. Invalid minutes and seconds are
rejected. The border flashes yellow when the countdown finishes.

```toml
[widgets.timer]
kind = "Timer"
```

### Stopwatch

`Stopwatch` provides Start, Stop, and Reset controls. Reset remains visible but
is disabled while the stopwatch is running.

```toml
[widgets.stopwatch]
kind = "Stopwatch"
```

### System monitor

`SystemMonitor` samples total CPU utilisation once per second. Its 38-sample
history graph uses green, yellow, and red threshold colours.

```toml
[widgets.system_monitor]
kind = "SystemMonitor"
```

### Weather

`Weather` uses Open-Meteo to display current conditions. No API key is needed.
The default location is Sydney, units are metric, and the refresh interval is
15 minutes. `units` accepts `metric` or `imperial`; the Refresh button requests
an immediate update.

```toml
[widgets.weather]
kind = "Weather"
opts = { location = "Perth", units = "metric", refresh_minutes = 10 }
```

The configured location is sent to Open-Meteo's geocoding and forecast APIs.
Network and response errors are shown inside the widget without stopping the
dashboard.

### Todo

`Todo` stores a title, optional notes, and an optional ISO-format due date in a
local SQLite database at `~/.local/state/dashify/todo.db`. Todos remain in
insertion order.

Select **Manage todos** to enter the widget's interaction context. Menus support
the arrow keys and these Vim-inspired bindings:

- `j` / `k`: move down / up
- `g` / `G`: move to the first / last option
- `l` or `Enter`: select
- `Esc`: go back

Dashify asks before creating the database. Todo deletion and database deletion
are permanent; deleting the database requires a separate warning screen.

```toml
[widgets.todos]
kind = "Todo"
```

### Custom

`Custom` is a single-layer vertical arrangement. Its Boolean switches enable
available elements in a fixed order; `text` adds a short heading and `timezone`
configures an enabled clock. Each enabled widget otherwise retains its built-in
defaults.

```toml
[widgets.focus]
kind = "Custom"
opts = { text = "Focus", clock = true, timezone = "UTC", timer = true, weather = true }
```

Available switches are `clock`, `timer`, `stopwatch`, `system_monitor`, `todo`,
and `weather`. Horizontal custom layouts are intentionally unsupported; use an
`HBox` in the main widget tree instead.

## Development

Install the development dependencies and run all release checks with:

```console
poetry install
poetry run ruff check
poetry run ruff format
poetry run pyright
poetry run pytest
poetry check
poetry build
```

Source files live in `src`, tests in `tests`, and the documented default layout
in `defaults/dashify.toml`.

## Licence

Dashify is released under the MIT Licence. See `LICENSE`.
