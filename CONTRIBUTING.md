# Contributing

Thanks for helping improve the WyreStorm NetworkHD integration. Bug reports and feature requests go in
[GitHub Issues](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/issues).

## Development setup

You need Python 3.14 (what current Home Assistant requires), Git and, optionally, Make.

```bash
git clone https://github.com/Matt-Hadley/wyrestorm-networkhd-ha.git
cd wyrestorm-networkhd-ha
```

Then set up a virtual environment in `.venv` with one of:

```bash
# Make (creates .venv, installs dev dependencies and the pre-commit hooks)
make install

# uv
uv venv --python 3.14
uv pip install -e ".[dev]"

# venv + pip
python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip setuptools
.venv/bin/pip install -e ".[dev]"
```

Without Make, install the pre-commit hooks with `.venv/bin/pre-commit install`.

The integration depends on the [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) library
(`wyrestorm-networkhd>=3.1.2,<4` in `manifest.json`).

## Running tests

Tests use
[pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component), which
provides the `hass` fixture and a real Home Assistant core. The controller is mocked: the tests feed library models
parsed from `tests/custom_components/wyrestorm_networkhd/fixtures/controller_responses.json`.

```bash
make test        # all tests; coverage reports go to htmlcov/ and coverage.xml

# or directly
.venv/bin/pytest -q
.venv/bin/pytest tests/custom_components/wyrestorm_networkhd/test_services.py -v
```

The entities each platform creates (entity IDs, unique IDs, categories, device classes) are listed in
`EXPECTED_ENTITIES` in `tests/custom_components/wyrestorm_networkhd/test_init.py`; update it with any intended entity
change.

Fixture data must stay anonymised: documentation IP addresses (192.0.2.0/24), made-up MAC addresses and generic aliases.

## Code quality

```bash
make format   # Ruff format + autofix
make lint     # Ruff lint
make check    # Ruff lint, MyPy (strict), Prettier (needs Node.js), Vulture, Bandit; fails on any error
make help     # all targets
```

Pre-commit runs the same checks on commit. Code style is Ruff with a 120-character line length, type hints on all
function signatures and docstrings on public methods.

`translations/en.json` must stay identical to `strings.json`; after editing `strings.json`, run
`cp custom_components/wyrestorm_networkhd/strings.json custom_components/wyrestorm_networkhd/translations/en.json`.

[CLAUDE.md](CLAUDE.md) describes the architecture (coordinator, refresh rules, entities and services).

## Pull requests

1. Branch from `main` (`feat/...`, `fix/...`, `docs/...`).
2. Add or update tests for your change and make sure `make test` and `make check` pass. CI runs the same checks
   (`make health-check`, plus HACS and hassfest validation), and `main` requires them to pass before merging.
3. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, with
   `!` for breaking changes). Release Please uses them to version releases and write the changelog.
4. Open a pull request against `main`.

## Testing with real hardware

`docker-compose.yml` starts a Home Assistant container with the integration mounted from `custom_components/`. Never
commit controller addresses, credentials, MAC addresses or site-specific aliases.

## Security issues

Do not open public issues for security vulnerabilities; see [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
