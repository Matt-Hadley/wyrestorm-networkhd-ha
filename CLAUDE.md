# Claude Code Assistant Instructions

## 🎯 Integration Overview
This is a Home Assistant integration for WyreStorm NetworkHD matrix switching systems. It uses SSH to communicate with the controller and provides entities for monitoring and control.

## 🏗️ Architecture Guidelines

### Coordinator Pattern
- `WyreStormCoordinator` (coordinator.py) owns the SSH client and makes every API call; it is stored on `entry.runtime_data` (`WyreStormConfigEntry`).
- Entities NEVER call the API directly: use `async_set_matrix`, `async_set_power`, `async_reboot`.
- `_async_setup` connects and registers the `endpoint`/`video` notification callbacks; `async_shutdown` unregisters them and disconnects under the lock.
- Every API exchange holds `coordinator._lock` (the controller handles one command/response at a time).
- Catch `API_ERRORS` (`NetworkHDError`, `OSError`, `ValueError`), never match exception message strings. Commands raise `HomeAssistantError(translation_key="command_failed")`.

### Refresh Rules
1. **Polling** is a fixed 60 s fallback (`DEFAULT_UPDATE_INTERVAL`; core does not allow a polling interval field, see the appropriate-polling rule); `iot_class` is `local_push`.
2. **Notifications** (endpoint online/offline, video found/lost) call `async_request_refresh()` via a background task; HA's debouncer collapses bursts.
3. **Matrix changes** (`async_set_matrix`) re-read only `matrix get`.
4. **Display power**: no refresh (it does not change device status).
5. **Device info** is cached on the coordinator for 10 minutes (monotonic timestamp) and invalidated by endpoint notifications.
6. **Link loss**: a failed update raises `UpdateFailed` (entities go unavailable; DataUpdateCoordinator logs once on loss and once on recovery) and disconnects; the next update or command reconnects (`_ensure_connected`, under the lock). Rejected credentials raise `ConfigEntryAuthFailed` (reauth flow).
7. **Matrix changes** update `self.data` and call `async_update_listeners()` (not `async_set_updated_data`, which would cancel a pending debounced refresh and reset the poll timer). The reboot button marks the coordinator failed until the next successful update.

### Devices and Entities
- The controller device is registered in `async_setup_entry` with identifier `(DOMAIN, coordinator.controller_id)` (the entry unique_id); endpoint devices use `(DOMAIN, true_name)`, their MAC as a connection, and `via_device_id=coordinator.controller_device_id`.
- The SSH API exposes no MAC/serial, so the unique_id is the controller MAC (12 lowercase hex digits) from its mDNS instance name (`mdns.py`: unicast PTR query for `_workstation._tcp.local.` to host:5353, or the zeroconf discovery name). A controller that does not answer is identified by its host; `async_setup_entry` retries the lookup at every setup and then moves the unique_id, the controller device identifier and the reboot button unique_id (`async_move_controller_id`). Reconfigure keeps a MAC id (aborts `wrong_device` if the new host announces another MAC); a host id moves to the new MAC or host.
- Endpoints missing from device status/info (usually offline) are kept: the Controller link sensor shows off, the other entities are unavailable.
- Devices of the entry that the controller stops reporting (an endpoint removed from the controller, a controller device left from an old host) are removed after `STALE_REFRESHES` (3) successful refreshes in a row without them, never while the controller reports no endpoints at all. `async_remove_config_entry_device` lets users delete a device that is not currently reported.
- Platforms add endpoint entities through `async_add_endpoint_entities` (entity.py): a coordinator listener adds entities for endpoints that appear after setup, and forgets endpoints whose device was removed so they are added again if they return.
- Endpoint entities subclass `WyreStormEndpointEntity` (entity.py); names come from `translation_key` in strings.json, icons from icons.json.

### Discovery
`manifest.json` matches `_workstation._tcp.local.` instances named `nhd-*ctl*` (HA lowercases names before fnmatch). `async_step_zeroconf` takes the MAC from the instance name, updates the host of a known entry (the pinned host key stays, so another device at that address is still refused), aborts for an entry known by host, and otherwise asks for credentials in `zeroconf_confirm` (then the same TOFU host key confirmation as the user step).

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
├── config_flow.py           # User, zeroconf, reconfigure and reauth flows
├── mdns.py                  # Controller MAC from its mDNS name (unicast PTR lookup)
├── diagnostics.py           # Redacted diagnostics
├── const.py                 # Constants
├── services.yaml, strings.json, translations/en.json, icons.json
├── brand/icon.png           # Local brand image (HA >= 2026.3)
├── _utils_coordinator.py    # Builds device collections / matrix mapping
├── models/                  # The endpoint fields entities read (no business logic)
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
- A full refresh sends five commands (four when device info is cached). Keep targeted paths (matrix-only refresh, no refresh after display power) targeted.

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