"""Home Assistant test fixtures.

Library responses are built by the library's own parse() from raw controller replies
(fixtures/controller_responses.json, an anonymised capture from a real NHD-000-CTL), so these
tests also exercise the contract between this integration and wyrestorm-networkhd.
"""

import json
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus, IpSetting, Matrix, Version

from custom_components.wyrestorm_networkhd.const import DOMAIN

HOST = "192.0.2.10"
ENTRY_DATA = {CONF_HOST: HOST, CONF_USERNAME: "wyrestorm", CONF_PASSWORD: "networkhd", CONF_PORT: 10022}
RAW: dict[str, str] = json.loads((Path(__file__).parent / "fixtures" / "controller_responses.json").read_text())


def parsed_responses(raw: dict[str, str] = RAW) -> dict[str, Any]:
    """Return api_query method name -> parsed library model."""
    return {
        "config_get_version": Version.parse(raw["config get version"]),
        "config_get_ipsetting": IpSetting.parse(raw["config get ipsetting"]),
        "config_get_devicejsonstring": DeviceJsonString.parse(raw["config get devicejsonstring"]),
        "config_get_device_status": DeviceStatus.parse(raw["config get device status"]),
        "config_get_device_info": DeviceInfo.parse(raw["config get device info"]),
        "matrix_get": Matrix.parse(raw["matrix get"]),
    }


class FakeNotificationHandler:
    """Stands in for client.notification_handler."""

    def __init__(self) -> None:
        self.callbacks: dict[str, list] = defaultdict(list)

    def register_callback(self, notification_type: str, callback) -> None:
        self.callbacks[notification_type].append(callback)

    def unregister_callback(self, notification_type: str, callback) -> None:
        self.callbacks[notification_type].remove(callback)

    def fire(self, notification_type: str, notification: Any) -> None:
        for callback in list(self.callbacks[notification_type]):
            callback(notification)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in every test."""


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Patch the SSH client and NHDAPI; `mock_client.api` is the fake API."""
    client = AsyncMock()
    client.is_connected = Mock(return_value=True)
    client.notification_handler = FakeNotificationHandler()
    client.api = api = AsyncMock()
    for name, value in parsed_responses().items():
        getattr(api.api_query, name).return_value = value
    with (
        patch("custom_components.wyrestorm_networkhd.coordinator.NetworkHDClientSSH", return_value=client),
        patch("custom_components.wyrestorm_networkhd.coordinator.NHDAPI", return_value=api),
        patch("custom_components.wyrestorm_networkhd.config_flow.NHDAPI", return_value=api),
    ):
        yield client


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry added to hass."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=HOST, title=f"WyreStorm NetworkHD ({HOST})", data=ENTRY_DATA)
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> MockConfigEntry:
    """Set up the integration with the mocked controller."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
