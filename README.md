# CIRADA SENPY

[![unit](https://github.com/JavierArredondo/cirada_senpy/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/JavierArredondo/cirada_senpy/actions/workflows/unit_tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

The **CIRADA** cutout **SE**rvice i**N** **PY**thon is a small package and CLI to
batch-download radio-astronomy cutouts from the [CIRADA](http://cutouts.cirada.ca/)
RM cutout server, given a list of coordinates or source names.

It takes a table of targets (CSV / Parquet / Pickle), queries the portal for each
one, and writes the returned FITS bundles to disk — with a progress bar and a
skip-existing option for resumable runs.

> **Portal status (June 2026).** The CIRADA portal is reachable over **plain HTTP
> only** (`http://cutouts.cirada.ca/`; there is no TLS on port 443). The
> `rm_get_cutout` endpoint this package targets has been observed returning HTTP
> 500 — the public service may be partially down or its request format may have
> drifted since this client was written. See [Status & roadmap](#status--roadmap).

## Requirements

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) for development (recommended)

## Installation

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv pip install git+https://github.com/JavierArredondo/cirada_senpy.git
```

Or, from a clone, into the current environment:

```bash
git clone https://github.com/JavierArredondo/cirada_senpy.git
cd cirada_senpy
uv pip install .
```

## Usage

### Input format

The input is a table with `ra`, `dec`, and `name` columns. Coordinates may be
decimal degrees, sexagesimal strings, or left blank when a resolvable `name` is
given:

| ra          | dec         | name  |
|-------------|-------------|-------|
| 162.338077  | -0.66805    |       |
|             |             | M87   |
| '00 42 30   | +41 12 00'  |       |
| 05h 35m 18s | -05d 23m 0s | Orion |

A ready-to-use example lives at [`tests/unit/data/input_example.csv`](tests/unit/data/input_example.csv).

### CLI

```bash
senpy download <path_to_file> <path_to_output>
```

`<path_to_file>` may be a `.csv`, `.parquet`, or `.pkl`. Pass `--force` to skip
targets whose output `.tgz` already exists (useful for resuming an interrupted
batch):

```bash
senpy download <path_to_file> <path_to_output> --force
```

### Python API

```python
from cirada_senpy.core import download_file

download_file("input_example.csv", "/tmp/my_fits")
```

Open a downloaded `.tgz` bundle into a list of Astropy HDUs:

```python
from cirada_senpy.core import open_fits_tgz

fits_list = open_fits_tgz("/tmp/my_fits/Orion.tgz")
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for environment and dependency
management, and `pre-commit` (isort + black) for formatting.

```bash
# create the venv and install runtime + dev dependencies
uv sync --dev

# run the test suite
uv run pytest -q tests/unit/

# run with coverage (matches CI)
uv run coverage run --source cirada_senpy/ -m pytest tests/unit/
uv run coverage report

# install the git hooks
uv run pre-commit install
```

## Status & roadmap

This is a revived 2022 project. Current state:

- ✅ Modernized packaging (`pyproject.toml` + uv), CI on Python 3.10–3.12.
- ✅ Test suite passes against current `pandas` / `numpy` / `astropy`.
- ⚠️ The live `rm_get_cutout` endpoint returns HTTP 500 to this client. The unit
  tests mock the network, so green tests do **not** prove the portal round-trip
  still works end-to-end. The wire layer (hand-built multipart body + a
  fixed-offset slice of the JSON response) is fragile by design and is the most
  likely thing to need fixing.

Possible directions: harden the request/response layer (proper multipart, robust
JSON parsing, retries and error handling), and/or broaden beyond the RM cutout
server to the general multi-survey image service (VLASS, FIRST, NVSS, GLEAM,
WISE, PanSTARRS, SDSS).

## License

[MIT](LICENSE) © Javier Arredondo
