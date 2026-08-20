# EOL checker

EOL Checker retrieves software and hardware lifecycle information, stores it in a local SQLite cache, and provides command-line search. A refresh validates complete source datasets before atomically replacing the active cache, so an unsuccessful update leaves the prior cache intact.

## Installation

Install from PyPI with `pip` or, preferably for a command-line application, [`pipx`](https://pypa.github.io/pipx/):

```bash
pipx install eolchecker
```

The package supports Python 3.10 or later.

## Usage

Refresh is explicit. Run it before the first query and whenever current source data is required:

```bash
eolchecker --update
```

Search the cached data:

```bash
eolchecker --software nginx
eolchecker --hardware PowerEdge
```

Update and query in one command:

```bash
eolchecker --update --software nginx
```

The default cache path is `$XDG_CACHE_HOME/eolchecker/eol.db`, or `~/.cache/eolchecker/eol.db` when `XDG_CACHE_HOME` is unset. Use `--cache-path` to select another location:

```bash
eolchecker --cache-path /srv/eolchecker/eol.db --software nginx
```

Run `eolchecker --help` for all command options. Invoking the command without an operation displays help and does not access the network or create cache files.

## Data sources

Software lifecycle data is retrieved from the [endoflife.date v1 API](https://endoflife.date/docs/api/v1/). Hardware lifecycle data is parsed from the [Hardware Wartung website](https://www.hardwarewartung.com/en/). Upstream source changes or outages cause the update command to fail safely without replacing the active cache.
