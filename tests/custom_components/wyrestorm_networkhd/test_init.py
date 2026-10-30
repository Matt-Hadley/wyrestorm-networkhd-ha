"""Tests for setup, unload, the coordinator and entity availability."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed, snapshot_platform
from syrupy.assertion import SnapshotAssertion
from wyrestorm_networkhd.exceptions import ConnectionError as NHDConnectionError
from wyrestorm_networkhd.models.api_notifications import NotificationEndpoint, NotificationVideo
from wyrestorm_networkhd.models.api_query import DeviceJsonString, Matrix

from custom_components.wyrestorm_networkhd.const import DOMAIN
from custom_components.wyrestorm_networkhd.diagnostics import async_get_config_entry_diagnostics

from .conftest import HOST, RAW

LINK_RX1 = "binary_sensor.receiver_display1_controller_link"
VIDEO_TX1 = "binary_sensor.transmitter_source1_video_input"
SOURCE_RX1 = "select.receiver_display1_input_source"
POWER_ON_RX1 = "button.receiver_display1_display_power_on"
REBOOT = "button.wyrestorm_networkhd_192_0_2_10_reboot_controller"


async def test_setup_and_unload(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Setup connects and subscribes; unload unsubscribes and disconnects."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert set(mock_client.notification_handler.callbacks) == {"endpoint", "video"}
    assert hass.states.get(SOURCE_RX1).state == "Source2"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not any(mock_client.notification_handler.callbacks.values())
    mock_client.disconnect.assert_awaited()


@pytest.mark.parametrize("fail", ["connect", "query"])
async def test_setup_not_ready(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock, fail: str
) -> None:
    """An unreachable or misbehaving controller retries setup later."""
    if fail == "connect":
        mock_client.connect.side_effect = NHDConnectionError("refused")
    else:
        mock_client.api.api_query.config_get_device_status.side_effect = ValueError("No 'devices status' key")
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("platform", [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT])
async def test_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_client: MagicMock,
    snapshot: SnapshotAssertion,
    platform: Platform,
) -> None:
    """Snapshot each platform's entities; endpoint devices hang off the controller device."""
    with patch("custom_components.wyrestorm_networkhd.PLATFORMS", [platform]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    await snapshot_platform(hass, er.async_get(hass), snapshot, config_entry.entry_id)

    dev_reg = dr.async_get(hass)
    controller = dev_reg.async_get_device_by_identifier((DOMAIN, HOST), config_entry.entry_id)
    rx = dev_reg.async_get_device_by_identifier((DOMAIN, "NHD-400-RX-E4CE02BB0001"), config_entry.entry_id)
    assert rx.via_device_id == controller.id


async def test_drop_unavailable_reconnect(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_client: MagicMock,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A dropped link makes entities unavailable (logged once); the next poll reconnects."""
    connects = mock_client.connect.await_count
    mock_client.is_connected.return_value = False
    mock_client.connect.side_effect = NHDConnectionError("no route")

    for _ in range(2):
        freezer.tick(timedelta(seconds=61))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert hass.states.get(LINK_RX1).state == STATE_UNAVAILABLE
    assert hass.states.get(REBOOT).state == STATE_UNAVAILABLE
    assert caplog.text.count("Error fetching WyreStorm NetworkHD data") == 1

    mock_client.connect.side_effect = None
    mock_client.connect.side_effect = lambda: mock_client.is_connected.configure_mock(return_value=True)
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert mock_client.connect.await_count == connects + 3
    assert hass.states.get(LINK_RX1).state == STATE_ON
    assert "Fetching WyreStorm NetworkHD data recovered" in caplog.text


async def test_offline_endpoint(hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock) -> None:
    """An offline endpoint missing from status/info is kept: link off, other entities unavailable."""
    query = mock_client.api.api_query
    json_list = DeviceJsonString.parse(RAW["config get devicejsonstring"])
    json_list[0].online = False  # Display1
    query.config_get_devicejsonstring.return_value = json_list
    query.config_get_device_status.return_value = [
        d for d in query.config_get_device_status.return_value if d.aliasname != "Display1"
    ]
    query.config_get_device_info.return_value = [
        d for d in query.config_get_device_info.return_value if d.aliasname != "Display1"
    ]

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(LINK_RX1).state == STATE_OFF
    assert hass.states.get(SOURCE_RX1).state == STATE_UNAVAILABLE
    assert hass.states.get(POWER_ON_RX1).state == STATE_UNAVAILABLE


async def test_notifications_trigger_debounced_refresh(
    freezer: FrozenDateTimeFactory, hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """A burst of notifications triggers a refresh that picks up the new state."""
    query = mock_client.api.api_query
    calls = query.config_get_device_status.await_count
    status = query.config_get_device_status.return_value
    tx1 = next(d for d in status if d.aliasname == "Source1")
    tx1.hdmi_in_frame_rate = 0
    assert hass.states.get(VIDEO_TX1).state == STATE_ON

    handler = mock_client.notification_handler
    handler.fire("video", NotificationVideo(status="lost", device="Source1"))
    handler.fire("video", NotificationVideo(status="lost", device="Source1"))
    handler.fire("endpoint", NotificationEndpoint(online=True, device="Source1"))
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=11))  # past the request-refresh cooldown
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(VIDEO_TX1).state == STATE_OFF
    assert query.config_get_device_status.await_count <= calls + 2  # 3 notifications, debounced
    assert query.config_get_device_info.await_count == 2  # endpoint notification invalidated the cache


async def test_select_source(hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock) -> None:
    """Selecting a source routes it and refreshes only the matrix."""
    api = mock_client.api
    api.api_query.matrix_get.return_value = Matrix.parse("matrix information:\nSource1 Display1\nSource2 Display2")
    await hass.services.async_call(
        "select", SERVICE_SELECT_OPTION, {ATTR_ENTITY_ID: SOURCE_RX1, ATTR_OPTION: "Source1"}, blocking=True
    )
    api.media_stream_matrix_switch.matrix_set.assert_awaited_once_with("Source1", ["Display1"])
    assert hass.states.get(SOURCE_RX1).state == "Source1"

    api.api_query.matrix_get.return_value = Matrix.parse("matrix information:\nNULL Display1\nSource2 Display2")
    await hass.services.async_call(
        "select", SERVICE_SELECT_OPTION, {ATTR_ENTITY_ID: SOURCE_RX1, ATTR_OPTION: "None"}, blocking=True
    )
    api.media_stream_matrix_switch.matrix_set_null.assert_awaited_once_with(["Display1"])
    assert hass.states.get(SOURCE_RX1).state == "None"


async def test_buttons(hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock) -> None:
    """Buttons go through the coordinator; failures raise HomeAssistantError."""
    api = mock_client.api
    await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: POWER_ON_RX1}, blocking=True)
    api.connected_device_control.config_set_device_sinkpower.assert_awaited_once_with(power="on", rx=["Display1"])

    await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: REBOOT}, blocking=True)
    api.reboot_reset.set_reboot.assert_awaited_once()
    mock_client.disconnect.assert_awaited()  # next poll reconnects

    api.reboot_reset.set_reboot.side_effect = TimeoutError()
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: REBOOT}, blocking=True)
    assert err.value.translation_key == "command_failed"


async def test_diagnostics(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """Diagnostics redact the host, credentials and addresses."""
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert HOST not in str(diag)
    assert "networkhd" not in str(diag["entry"]["data"])
    assert diag["data"]["device_controller"]["core_version"] == "9.4.13"
