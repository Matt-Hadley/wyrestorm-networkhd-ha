# Claude Code Assistant Instructions

## 🎯 Integration Overview
This is a Home Assistant integration for WyreStorm NetworkHD matrix switching systems. It uses SSH to communicate with the controller and provides entities for monitoring and control.

## 🏗️ Architecture Guidelines

### Coordinator Pattern
- The `WyreStormCoordinator` handles all API communication
- Entities should NEVER call the API directly
- Use `async_selective_refresh()` for targeted updates

### API Optimization Rules
1. **Video input changes**: Only refresh matrix assignments
   ```python
   await coordinator.async_selective_refresh(["matrix_assignments"])
   ```

2. **Display power operations**: No refresh needed (doesn't affect device status)
   
3. **Device info**: Automatically cached for 10 minutes via decorator

4. **Real-time notifications**: Automatic selective refresh on events
   - Device online/offline → refreshes device_jsonstring
   - Video found/lost → refreshes matrix_assignments

### Caching Strategy
Use the `@cache_for_seconds` decorator for rarely-changing data:
```python
@cache_for_seconds(600)  # 10 minutes
async def get_expensive_data(self):
    return await self.api.expensive_call()
```

## 🧪 Testing Commands
```bash
# Run all tests with coverage
make test-cov

# Quick test run
.venv/bin/pytest tests/ --tb=no --no-cov -q

# Run specific test file
.venv/bin/pytest tests/custom_components/wyrestorm_networkhd/test_coordinator.py -v

# Run with specific pattern
.venv/bin/pytest -k "test_matrix" -v
```

## 📁 File Structure
```
custom_components/wyrestorm_networkhd/
├── __init__.py              # Integration setup and services
├── coordinator.py           # Main data coordinator with selective refresh
├── config_flow.py           # Configuration UI flow
├── const.py                # Constants (well-documented)
├── services.yaml           # Service definitions for HA UI
├── _cache_utils.py         # Caching decorator utility
├── _utils_coordinator.py   # Coordinator helper functions
├── models/                 # Data models (no business logic)
│   ├── coordinator.py      # CoordinatorData class
│   ├── device_controller.py # Controller device model
│   └── device_receiver_transmitter.py # Device models
├── binary_sensor.py        # Online/video activity sensors
├── button.py              # Display power control buttons
└── select.py              # Input source selection
```

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
4. **Don't modify models after creation** - Models are data containers only
5. **Don't bypass selective refresh** - Use coordinator methods for all operations

## 🔧 Development Workflow
1. Make changes to relevant files
2. Run `make lint` to check code style (pre-commit hooks will run)
3. Run `make test` to verify functionality
4. Check `make test-cov` for coverage (aim for >80%)
5. Update docstrings if you add public methods
6. Test with actual hardware if possible

## 📊 Performance Guidelines
- **Full refresh**: ~800ms (all API calls)
- **Matrix assignment refresh**: ~200ms
- **Device status refresh**: ~300ms  
- **Cached device info**: <1ms
- **Target UI response**: <100ms after user action

### API Call Optimization
- Video input changes: Only 1x matrix_get (was 2x)
- Display power: 0 API calls (was full refresh)
- Device info: 1 call per 10 minutes (was every poll)

## 🐛 Debugging Tips
- Enable debug logging: Set logger `custom_components.wyrestorm_networkhd` to `debug`
- Check SSH connection: Look for "Device connection successful" in logs
- Monitor API calls: Watch for "Fetching" messages in debug logs
- Use selective refresh logs to verify optimization: "Starting selective data refresh for: ['matrix_assignments']"

## 🧩 Adding New Features

### New Entity Type
1. Create new platform file (e.g., `sensor.py`)
2. Add platform to `PLATFORMS` in `const.py`
3. Follow existing entity patterns (inherit from `CoordinatorEntity`)
4. Add comprehensive tests in `tests/` directory

### New API Optimization
1. Add new option to `async_selective_refresh()`
2. Document performance impact in docstring
3. Add caching decorator if data changes rarely
4. Update CLAUDE.md with new optimization

### New Service
1. Add service definition to `services.yaml`
2. Implement service handler in `__init__.py`
3. Add service constants to `const.py`
4. Follow validation patterns from existing services

## 🔍 Code Review Checklist
- [ ] All public methods have comprehensive docstrings
- [ ] Type hints are complete and accurate
- [ ] No direct API calls from entities (use coordinator)
- [ ] Appropriate use of selective refresh or caching
- [ ] Tests cover new functionality
- [ ] Error handling for offline devices
- [ ] Logging at appropriate levels
- [ ] Performance impact considered and documented