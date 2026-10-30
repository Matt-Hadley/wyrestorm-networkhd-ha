"""Tests for setup, unload, the coordinator and entity availability."""

import asyncio
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from wyrestorm_networkhd.exceptions import (
    AuthenticationError,
    ConnectionError as NHDConnectionError,
)
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


RX = "wyrestorm_networkhd_NHD-400-RX-E4CE02BB000"
TX = "wyrestorm_networkhd_NHD-400-TX-E4CE02AA000"
DIAG, CONF = er.EntityCategory.DIAGNOSTIC, er.EntityCategory.CONFIG
# entity_id -> (unique_id, entity_category, original_device_class, translation_key)
EXPECTED_ENTITIES = {
    Platform.BINARY_SENSOR: {
        **{
            f"binary_sensor.receiver_display{n}_controller_link": (
                f"{RX}{n}_controller_link",
                DIAG,
                "connectivity",
                "controller_link",
            )
            for n in (1, 2)
        },
        **{
            f"binary_sensor.receiver_display{n}_video_output": (
                f"{RX}{n}_video_output",
                None,
                "running",
                "video_output",
            )
            for n in (1, 2)
        },
        **{
            f"binary_sensor.transmitter_source{n}_controller_link": (
                f"{TX}{n}_controller_link",
                DIAG,
                "connectivity",
                "controller_link",
            )
            for n in (1, 2)
        },
        **{
            f"binary_sensor.transmitter_source{n}_video_input": (f"{TX}{n}_video_input", None, "running", "video_input")
            for n in (1, 2)
        },
    },
    Platform.BUTTON: {
        **{
            f"button.receiver_display{n}_display_power_{s}": (
                f"{RX}{n}_display_power_{s}",
                None,
                None,
                f"display_power_{s}",
            )
            for n in (1, 2)
            for s in ("on", "off")
        },
        "button.wyrestorm_networkhd_192_0_2_10_reboot_controller": (
            "wyrestorm_networkhd_192.0.2.10_controller_reboot",
            CONF,
            "restart",
            "controller_reboot",
        ),
    },
    Platform.SELECT: {
        f"select.receiver_display{n}_input_source": (f"{RX}{n}_source", None, None, "source") for n in (1, 2)
    },
}


@pytest.mark.parametrize("platform", list(EXPECTED_ENTITIES))
async def test_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_client: MagicMock,
    platform: Platform,
) -> None:
    """Each platform creates the expected entities; endpoint devices hang off the controller device."""
    with patch("custom_components.wyrestorm_networkhd.PLATFORMS", [platform]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    entries = er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
    actual = {
        e.entity_id: (e.unique_id, e.entity_category, e.original_device_class, e.translation_key) for e in entries
    }
    assert actual == EXPECTED_ENTITIES[platform]
    for entity_id in actual:
        assert hass.states.get(entity_id).state != STATE_UNAVAILABLE

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
    mock_client.disconnect.assert_awaited()
    assert hass.states.get(REBOOT).state == STATE_UNAVAILABLE  # until an update reconnects
    assert hass.states.get(LINK_RX1).state == STATE_UNAVAILABLE

    await setup_integration.runtime_data.async_refresh()
    assert hass.states.get(LINK_RX1).state == STATE_ON

    api.reboot_reset.set_reboot.side_effect = TimeoutError()
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: REBOOT}, blocking=True)
    assert err.value.translation_key == "command_failed"


async def test_diagnostics(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """Diagnostics redact the host, credentials and addresses."""
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert HOST not in str(diag)
    assert "networkhd" not in str(diag["entry"]["data"])
    assert diag["data"]["version"]["core_version"] == "9.4.13"
    assert diag["device_info"][0]["mac"] == "**REDACTED**"
    assert diag["device_status"][0]["name"].startswith("NHD-400-")


async def test_setup_auth_failed_starts_reauth(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Rejected credentials stop retrying and start a reauth flow."""
    mock_client.connect.side_effect = AuthenticationError("wyrestorm", HOST)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [f["context"]["source"] for f in flows] == [SOURCE_REAUTH]


async def test_update_auth_failed_starts_reauth(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock, freezer: FrozenDateTimeFactory
) -> None:
    """Credentials rejected on reconnect start a reauth flow."""
    mock_client.is_connected.return_value = False
    mock_client.connect.side_effect = AuthenticationError("wyrestorm", HOST)
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(LINK_RX1).state == STATE_UNAVAILABLE
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [f["context"]["source"] for f in flows] == [SOURCE_REAUTH]


async def test_commands_reconnect(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """A command after a dropped link reconnects first."""
    connects = mock_client.connect.await_count
    mock_client.is_connected.return_value = False
    await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: POWER_ON_RX1}, blocking=True)
    await hass.services.async_call(
        "select", SERVICE_SELECT_OPTION, {ATTR_ENTITY_ID: SOURCE_RX1, ATTR_OPTION: "Source1"}, blocking=True
    )
    assert mock_client.connect.await_count == connects + 2
    mock_client.api.connected_device_control.config_set_device_sinkpower.assert_awaited_once()

    mock_client.connect.side_effect = NHDConnectionError("no route")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call("button", SERVICE_PRESS, {ATTR_ENTITY_ID: POWER_ON_RX1}, blocking=True)
    assert err.value.translation_key == "command_failed"


async def test_select_keeps_poll_schedule(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock, freezer: FrozenDateTimeFactory
) -> None:
    """A matrix change updates entities without postponing the next poll."""
    query = mock_client.api.api_query
    polls = query.config_get_device_status.await_count
    freezer.tick(timedelta(seconds=40))
    async_fire_time_changed(hass)
    query.matrix_get.return_value = Matrix.parse("matrix information:\nSource1 Display1\nSource2 Display2")
    await hass.services.async_call(
        "select", SERVICE_SELECT_OPTION, {ATTR_ENTITY_ID: SOURCE_RX1, ATTR_OPTION: "Source1"}, blocking=True
    )
    assert hass.states.get(SOURCE_RX1).state == "Source1"
    assert query.config_get_device_status.await_count == polls

    freezer.tick(timedelta(seconds=25))  # 65 s after the last full refresh
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert query.config_get_device_status.await_count == polls + 1


async def test_select_readback_failure_refreshes(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """A switch that succeeded is not reported as failed when only the matrix read-back fails."""
    query = mock_client.api.api_query
    polls = query.config_get_device_status.await_count
    matrix = Matrix.parse("matrix information:\nSource1 Display1\nSource2 Display2")
    query.matrix_get.side_effect = [NHDConnectionError("dropped"), matrix]
    await hass.services.async_call(
        "select", SERVICE_SELECT_OPTION, {ATTR_ENTITY_ID: SOURCE_RX1, ATTR_OPTION: "Source1"}, blocking=True
    )
    await hass.async_block_till_done()

    assert query.config_get_device_status.await_count == polls + 1  # full refresh instead
    assert hass.states.get(SOURCE_RX1).state == "Source1"


async def test_unload_waits_for_exchange(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Unload disconnects only after the exchange holding the lock has finished."""
    lock = setup_integration.runtime_data._lock
    await lock.acquire()
    disconnects = mock_client.disconnect.await_count
    unload = hass.async_create_task(hass.config_entries.async_unload(setup_integration.entry_id))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert mock_client.disconnect.await_count == disconnects

    lock.release()
    assert await unload
    assert mock_client.disconnect.await_count == disconnects + 1
