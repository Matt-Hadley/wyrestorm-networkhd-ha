# Claude Code Assistant Instructions

## 🎯 Integration Overview
This is a Home Assistant integration for WyreStorm NetworkHD matrix switching systems. It uses SSH to communicate with the controller and provides entities for monitoring and control.

## 🏗️ Architecture Guidelines

### Coordinator Pattern
- `WyreStormCoordinator` (coordinator.py) owns the SSH client and makes every API call; it is stored on `entry.runtime_data` (`WyreStormConfigEntry`).
- Entities NEVER call the API directly: use `async_set_matrix`, `async_set_power`, `async_reboot`.
- `_async_setup` connects and registers the `endpoint`/`video` notification callbacks; `async_shutdown` unregisters them and disconnects.
- Every API exchange holds `coordinator._lock` (the controller handles one command/response at a time).
- Catch `API_ERRORS` (`NetworkHDError`, `OSError`, `ValueError`), never match exception message strings. Commands raise `HomeAssistantError(translation_key="command_failed")`.

### Refresh Rules
1. **Polling** is a fallback (`update_interval` option, default 60 s); `iot_class` is `local_push`.
2. **Notifications** (endpoint online/offline, video found/lost) call `async_request_refresh()` via a background task; HA's debouncer collapses bursts.
3. **Matrix changes** (`async_set_matrix`) re-read only `matrix get`.
4. **Display power**: no refresh (it does not change device status).
5. **Device info** is cached on the coordinator for 10 minutes (monotonic timestamp) and invalidated by endpoint notifications.
6. **Link loss**: a failed update raises `UpdateFailed` (entities go unavailable; DataUpdateCoordinator logs once on loss and once on recovery) and disconnects; the next update reconnects.

### Devices and Entities
- The controller device is registered in `async_setup_entry` with identifier `(DOMAIN, host)`; endpoint devices use `(DOMAIN, true_name)` and `via_device_id=coordinator.controller_device_id`.
- The controller API exposes no MAC/serial, so the config entry unique_id is the host. Reconfigure with a new host moves the unique_id, the controller device identifier and the reboot button unique_id.
- Endpoints missing from device status/info (usually offline) are kept: the Controller link sensor shows off, the other entities are unavailable.
- Endpoint entities subclass `WyreStormEndpointEntity` (entity.py); names come from `translation_key` in strings.json, icons from icons.json.

### Services
`matrix_set` (`source_device` optional = disconnect, `target_device`) and `power_control` (`devices`, `power_state`) are registered once in `async_setup` (services.py). Devices are matched by alias or true name; the controller is the one loaded entry that has all of them, or `config_entry_id` when ambiguous. Bad input raises `ServiceValidationError`.

### Translations
`translations/en.json` must stay identical to `strings.json` (custom integrations do not get strings.json compiled): `cp strings.json translations/en.json`. Do not use `[%key:...%]` references.

## 🧪 Testing Commands
```bash
# Run all tests with coverage
make test-cov

# Quick test run
.venv/bin/pytest tests/ --tb=no --no-cov -q

# Run specific test file
.venv/bin/pytest tests/custom_components/wyrestorm_networkhd/test_init.py -v

# Run with specific pattern
.venv/bin/pytest -k "test_matrix" -v
```

## 📁 File Structure
```
custom_components/wyrestorm_networkhd/
├── __init__.py              # Setup/unload, controller device, service registration
├── coordinator.py           # Connection, polling, notifications, commands
├── services.py              # matrix_set / power_control
├── entity.py                # Base entity for endpoint devices
├── config_flow.py           # User, reconfigure and options flows
├── diagnostics.py           # Redacted diagnostics
├── const.py                 # Constants
├── services.yaml, strings.json, translations/en.json, icons.json
├── brand/icon.png           # Local brand image (HA >= 2026.3)
├── _utils_coordinator.py    # Builds device collections / matrix mapping
├── models/                  # Data models (no business logic)
├── binary_sensor.py         # Controller link / video sensors
├── button.py                # Display power and controller reboot buttons
└── select.py                # Input source selection
```

HA-level tests (tests/custom_components/wyrestorm_networkhd/test_*.py) mock `NetworkHDClientSSH`/`NHDAPI` and feed library models parsed from `fixtures/controller_responses.json` (anonymised controller replies: documentation IPs, made-up MACs, generic aliases only).

## 📝 Code Style
- Use type hints for all function signatures
- Add docstrings to all public methods (see existing examples)
- Keep methods under 30 lines
- Prefer composition over inheritance
- Use descriptive variable names
- Add inline comments for complex logic

## ⚠️ Common Pitfalls
1. **Don't refresh after display power changes** - The display state doesn't affect device status
2. **Don't call API from entities** - Always go through the coordinator
3. **Don't forget to test with disconnected devices** - Handle offline devices gracefully
4. **Don't modify models after creation** - Models are data containers only (use `dataclasses.replace`)
5. **Don't send commands without `coordinator._lock`** - Interleaved commands corrupt responses

## 🔧 Development Workflow
1. Make changes to relevant files
2. Run `make lint` to check code style (pre-commit hooks will run)
3. Run `make test` to verify functionality
4. Check `make test-cov` for coverage (aim for >80%)
5. Update docstrings if you add public methods
6. Test with actual hardware if possible

## 📊 Performance Notes
- With library 2.2.x every command takes at least ~1 s (idle-gap response framing), and a full refresh sends six commands, so a full refresh takes several seconds. Keep targeted paths (matrix-only refresh, no refresh after display power) targeted.

## 🐛 Debugging Tips
- Enable debug logging: Set logger `custom_components.wyrestorm_networkhd` (and `wyrestorm_networkhd`) to `debug`
- Loss/recovery of the controller is logged once each by DataUpdateCoordinator ("Error fetching WyreStorm NetworkHD data" / "... recovered")
- Notifications are logged at debug as "Notification received"

## 🧩 Adding New Features

### New Entity Type
1. Create new platform file (e.g., `sensor.py`) with `PARALLEL_UPDATES`
2. Add platform to `PLATFORMS` in `const.py`
3. Subclass `WyreStormEndpointEntity`; add the name to `strings.json` (+ copy to `translations/en.json`) and icon to `icons.json`
4. Add HA-level tests and update EXPECTED_ENTITIES in test_init.py

### New Service
1. Add service definition to `services.yaml` and names/descriptions to `strings.json`
2. Implement the handler in `services.py` (resolve devices with `_resolve`) and the command in the coordinator
3. Raise `ServiceValidationError` for bad input, `HomeAssistantError` (translation_key) for controller failures

## 🔍 Code Review Checklist
- [ ] All public methods have comprehensive docstrings
- [ ] Type hints are complete and accurate
- [ ] No direct API calls from entities (use coordinator)
- [ ] API calls hold the coordinator lock and catch `API_ERRORS`
- [ ] Tests cover new functionality
- [ ] Error handling for offline devices
- [ ] Logging at appropriate levels
- [ ] Performance impact considered and documented