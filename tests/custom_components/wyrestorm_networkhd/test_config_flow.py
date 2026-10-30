"""Tests for the config flow."""

from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry
from wyrestorm_networkhd import HostKeyMismatchError
from wyrestorm_networkhd.exceptions import (
    AuthenticationError,
    ConnectionError as NHDConnectionError,
)

from custom_components.wyrestorm_networkhd.const import CONF_HOST_KEY_FINGERPRINT, DOMAIN

from .conftest import ENTRY_DATA, FINGERPRINT, HOST, OTHER_FINGERPRINT, PINNED_DATA

NEW_HOST = "192.0.2.20"


async def test_user_flow_confirms_presented_key(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Without a fingerprint, the presented key is shown for confirmation and then pinned (TOFU)."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_host_key"
    assert result["description_placeholders"]["fingerprint"] == FINGERPRINT
    assert "host_key_fingerprints" not in mock_client.ssh_cls.call_args.kwargs  # learning connect is unpinned

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"WyreStorm NetworkHD ({HOST})"
    assert result["data"] == PINNED_DATA
    assert result["result"].unique_id == HOST
    mock_client.disconnect.assert_awaited()


async def test_user_flow_no_key_reported(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """If the library reports no host key, the entry is created unpinned without a confirm step."""
    mock_client.host_key_fingerprint = None
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == ENTRY_DATA


@pytest.mark.parametrize(
    ("entered", "stored"),
    [
        (FINGERPRINT.removeprefix("SHA256:") + "=", [FINGERPRINT]),  # bare, padded
        (
            f"256 {FINGERPRINT} [{HOST}]:10022 (ECDSA)\n3072 {OTHER_FINGERPRINT} [{HOST}]:10022 (RSA)\n",
            [FINGERPRINT, OTHER_FINGERPRINT],
        ),
    ],
)
async def test_user_flow_supplied_fingerprint(
    hass: HomeAssistant, mock_client: MagicMock, entered: str, stored: list[str]
) -> None:
    """Supplied fingerprints are normalized, used for the connection test and stored without a confirm step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: entered}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: stored}
    assert mock_client.ssh_cls.call_args.kwargs["host_key_fingerprints"] == stored


async def test_user_flow_invalid_fingerprint(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """An unparseable fingerprint is a field error and nothing connects."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: "not a fingerprint"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOST_KEY_FINGERPRINT: "invalid_host_key_fingerprint"}
    mock_client.connect.assert_not_awaited()


async def test_user_flow_mismatch_shows_presented_key(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """A mismatching controller shows the presented fingerprint, which the user can then pin."""
    mock_client.connect.side_effect = HostKeyMismatchError(HOST, OTHER_FINGERPRINT)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: FINGERPRINT}
    )
    assert result["errors"] == {"base": "host_key_mismatch"}
    assert result["description_placeholders"]["fingerprint"] == OTHER_FINGERPRINT

    mock_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: OTHER_FINGERPRINT}
    )
    await hass.async_block_till_done()
    assert result["data"][CONF_HOST_KEY_FINGERPRINT] == [OTHER_FINGERPRINT]


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (AuthenticationError("wyrestorm", HOST), "invalid_auth"),
        (NHDConnectionError("refused"), "cannot_connect"),
        (TimeoutError(), "cannot_connect"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors_then_recover(
    hass: HomeAssistant, mock_client: MagicMock, side_effect: Exception, error: str
) -> None:
    """Connection failures map to form errors, and the flow recovers."""
    mock_client.connect.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["step_id"] == "confirm_host_key"


async def test_user_flow_duplicate(hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock) -> None:
    """A controller that is already configured aborts."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_new_host(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """Reconfiguring to a new host updates the unique id and keeps the controller device/entity."""
    entry = setup_integration
    dev_reg, ent_reg = dr.async_get(hass), er.async_get(hass)
    controller = dev_reg.async_get_device_by_identifier((DOMAIN, HOST), entry.entry_id)
    reboot_id = ent_reg.async_get_entity_id(Platform.BUTTON, DOMAIN, f"{DOMAIN}_{HOST}_controller_reboot")
    assert controller and reboot_id

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST, CONF_HOST_KEY_FINGERPRINT: FINGERPRINT}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == NEW_HOST
    assert entry.data == {**PINNED_DATA, CONF_HOST: NEW_HOST}
    assert entry.title == f"WyreStorm NetworkHD ({NEW_HOST})"
    assert dev_reg.async_get_device_by_identifier((DOMAIN, NEW_HOST), entry.entry_id).id == controller.id
    assert ent_reg.async_get_entity_id(Platform.BUTTON, DOMAIN, f"{DOMAIN}_{NEW_HOST}_controller_reboot") == reboot_id


async def test_reconfigure_same_host_error_then_success(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Reconfigure shows connection errors, then saves new credentials."""
    entry = setup_integration
    result = await entry.start_reconfigure_flow(hass)
    new_input = {**ENTRY_DATA, "password": "new", CONF_HOST_KEY_FINGERPRINT: FINGERPRINT}
    mock_client.connect.side_effect = NHDConnectionError("down")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], new_input)
    assert result["errors"] == {"base": "cannot_connect"}

    mock_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], new_input)
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {**PINNED_DATA, "password": "new"}
    assert entry.unique_id == HOST


async def test_reconfigure_host_collision(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """Reconfiguring onto another entry's host aborts."""
    MockConfigEntry(domain=DOMAIN, unique_id=NEW_HOST, data={**ENTRY_DATA, CONF_HOST: NEW_HOST}).add_to_hass(hass)
    result = await setup_integration.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert setup_integration.data[CONF_HOST] == HOST


async def test_reauth(hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock) -> None:
    """Reauth shows invalid_auth for wrong credentials, then saves the new ones and reloads."""
    entry = setup_integration
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_client.connect.side_effect = AuthenticationError("wyrestorm", HOST)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "wyrestorm", "password": "wrong"}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    mock_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"username": "admin", "password": "new"})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {**PINNED_DATA, "username": "admin", "password": "new"}


async def test_reconfigure_prefills_stored_fingerprint(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    """The reconfigure form suggests the stored fingerprint(s), one per line."""
    hass.config_entries.async_update_entry(
        setup_integration, data={**PINNED_DATA, CONF_HOST_KEY_FINGERPRINT: [FINGERPRINT, OTHER_FINGERPRINT]}
    )
    result = await setup_integration.start_reconfigure_flow(hass)
    field = next(k for k in result["data_schema"].schema if k == CONF_HOST_KEY_FINGERPRINT)
    assert field.description == {"suggested_value": f"{FINGERPRINT}\n{OTHER_FINGERPRINT}"}


async def test_reconfigure_edit_fingerprint(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """An edited fingerprint is validated, tested pinned and stored."""
    entry = setup_integration
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: "SHA256:???"}
    )
    assert result["errors"] == {CONF_HOST_KEY_FINGERPRINT: "invalid_host_key_fingerprint"}

    mock_client.connect.side_effect = HostKeyMismatchError(HOST, FINGERPRINT)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: OTHER_FINGERPRINT}
    )
    assert result["errors"] == {"base": "host_key_mismatch"}
    assert result["description_placeholders"]["fingerprint"] == FINGERPRINT
    assert mock_client.ssh_cls.call_args.kwargs["host_key_fingerprints"] == [OTHER_FINGERPRINT]

    mock_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: OTHER_FINGERPRINT}
    )
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST_KEY_FINGERPRINT] == [OTHER_FINGERPRINT]


async def test_reconfigure_clear_fingerprint_relearns(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Clearing the fingerprint connects unpinned and asks to confirm the presented key."""
    entry = setup_integration
    mock_client.host_key_fingerprint = OTHER_FINGERPRINT  # e.g. the controller was replaced
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["step_id"] == "confirm_host_key"
    assert result["description_placeholders"]["fingerprint"] == OTHER_FINGERPRINT
    assert "host_key_fingerprints" not in mock_client.ssh_cls.call_args.kwargs

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {**ENTRY_DATA, CONF_HOST_KEY_FINGERPRINT: [OTHER_FINGERPRINT]}


async def test_reauth_host_key_mismatch(
    hass: HomeAssistant, setup_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Reauth tests pinned and shows host_key_mismatch with the presented key."""
    result = await setup_integration.start_reauth_flow(hass)
    mock_client.connect.side_effect = HostKeyMismatchError(HOST, OTHER_FINGERPRINT)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"username": "a", "password": "b"})
    assert result["errors"] == {"base": "host_key_mismatch"}
    assert result["description_placeholders"]["fingerprint"] == OTHER_FINGERPRINT
    assert mock_client.ssh_cls.call_args.kwargs["host_key_fingerprints"] == [FINGERPRINT]
