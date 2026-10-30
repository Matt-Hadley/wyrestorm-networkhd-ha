"""Tests for the matrix_set and power_control services."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from wyrestorm_networkhd.exceptions import ResponseError

from custom_components.wyrestorm_networkhd.const import DOMAIN, SERVICE_MATRIX_SET, SERVICE_POWER_CONTROL

from .conftest import ENTRY_DATA, OTHER_FINGERPRINT, RAW, FakeNotificationHandler, parsed_responses

OTHER_HOST = "192.0.2.20"


async def test_matrix_set_by_alias_and_true_name(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Targets accept aliases and true names; a single string is accepted as a list."""
    switch = mock_client.api.media_stream_matrix_switch
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MATRIX_SET,
        {"source_device": "NHD-400-TX-E4CE02AA0001", "target_device": ["Display1", "NHD-400-RX-E4CE02BB0002"]},
        blocking=True,
    )
    switch.matrix_set.assert_awaited_once_with("Source1", ["Display1", "Display2"])

    await hass.services.async_call(DOMAIN, SERVICE_MATRIX_SET, {"target_device": "Display1"}, blocking=True)
    switch.matrix_set_null.assert_awaited_once_with(["Display1"])


async def test_power_control_by_alias_and_true_name(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """power_control resolves aliases and true names to receivers."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_POWER_CONTROL,
        {"devices": ["Display1", "NHD-400-RX-E4CE02BB0002"], "power_state": "off"},
        blocking=True,
    )
    mock_client.api.connected_device_control.config_set_device_sinkpower.assert_awaited_once_with(
        power="off", rx=["Display1", "Display2"]
    )


@pytest.mark.parametrize(
    ("service", "data", "key"),
    [
        (SERVICE_MATRIX_SET, {"source_device": "Nope", "target_device": "Display1"}, "device_not_found"),
        (SERVICE_MATRIX_SET, {"source_device": "Source1", "target_device": "Source2"}, "device_not_found"),
        (SERVICE_POWER_CONTROL, {"devices": "Nope", "power_state": "on"}, "device_not_found"),
        (
            SERVICE_POWER_CONTROL,
            {"config_entry_id": "missing", "devices": "Display1", "power_state": "on"},
            "entry_not_loaded",
        ),
    ],
)
async def test_validation_errors(
    hass: HomeAssistant, setup_integration: MockConfigEntry, service: str, data: dict, key: str
) -> None:
    """Unknown devices or entries raise ServiceValidationError."""
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, service, data, blocking=True)
    assert err.value.translation_key == key


async def test_schema_rejects_bad_power_state(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """power_state must be on or off."""
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_POWER_CONTROL, {"devices": "Display1", "power_state": "dim"}, blocking=True
        )


@pytest.mark.parametrize(
    ("service", "data"),
    [
        (SERVICE_MATRIX_SET, {"source_device": "Source1", "target_device": []}),
        (SERVICE_MATRIX_SET, {"source_device": "", "target_device": "Display1"}),
        (SERVICE_MATRIX_SET, {"source_device": None, "target_device": "Display1"}),
        (SERVICE_POWER_CONTROL, {"devices": [], "power_state": "on"}),
    ],
)
async def test_schema_rejects_empty_names(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock, service: str, data: dict
) -> None:
    """Empty device lists and an empty source are rejected instead of silently disconnecting."""
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, service, data, blocking=True)
    mock_client.api.media_stream_matrix_switch.matrix_set_null.assert_not_awaited()


async def test_command_failure(hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock) -> None:
    """A controller error raises a translated HomeAssistantError."""
    mock_client.api.media_stream_matrix_switch.matrix_set.side_effect = ResponseError("no mirror")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_MATRIX_SET, {"source_device": "Source1", "target_device": "Display1"}, blocking=True
        )
    assert err.value.translation_key == "command_failed"


async def test_two_controllers(hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock) -> None:
    """With two controllers, the one owning the devices is used; duplicates need config_entry_id."""
    other_client = AsyncMock()
    other_client.is_connected = Mock(return_value=True)
    other_client.notification_handler = FakeNotificationHandler()
    other_client.host_key_fingerprint = OTHER_FINGERPRINT
    other_api = AsyncMock()
    # Second controller: different hardware (true names); Display2 renamed so only it has "Office".
    raw = {k: v.replace("E4CE02", "E4CE03").replace("Display2", "Office") for k, v in RAW.items()}
    for name, value in parsed_responses(raw).items():
        getattr(other_api.api_query, name).return_value = value
    other = MockConfigEntry(domain=DOMAIN, unique_id=OTHER_HOST, data={**ENTRY_DATA, CONF_HOST: OTHER_HOST})
    other.add_to_hass(hass)
    with (
        patch("custom_components.wyrestorm_networkhd.coordinator.NetworkHDClientSSH", return_value=other_client),
        patch("custom_components.wyrestorm_networkhd.coordinator.NHDAPI", return_value=other_api),
    ):
        assert await hass.config_entries.async_setup(other.entry_id)
        await hass.async_block_till_done()

    sinkpower = "connected_device_control"
    await hass.services.async_call(
        DOMAIN, SERVICE_POWER_CONTROL, {"devices": "Office", "power_state": "on"}, blocking=True
    )
    getattr(other_api, sinkpower).config_set_device_sinkpower.assert_awaited_once_with(power="on", rx=["Office"])
    getattr(mock_client.api, sinkpower).config_set_device_sinkpower.assert_not_awaited()

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_POWER_CONTROL, {"devices": "Display1", "power_state": "on"}, blocking=True
        )
    assert err.value.translation_key == "device_ambiguous"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_POWER_CONTROL,
        {"config_entry_id": setup_integration.entry_id, "devices": "Display1", "power_state": "on"},
        blocking=True,
    )
    getattr(mock_client.api, sinkpower).config_set_device_sinkpower.assert_awaited_once_with(
        power="on", rx=["Display1"]
    )
