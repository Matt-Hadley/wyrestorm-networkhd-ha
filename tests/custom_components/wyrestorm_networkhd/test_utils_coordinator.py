"""Tests for merging the controller's device list, status and info into endpoint models."""

from dataclasses import replace

from wyrestorm_networkhd.models.api_query import DeviceInfo, DeviceJsonString, DeviceStatus

from custom_components.wyrestorm_networkhd._utils_coordinator import build_device_collections
from custom_components.wyrestorm_networkhd.models.device_receiver_transmitter import DeviceReceiver, DeviceTransmitter

from .conftest import RAW

RX1, TX1 = "NHD-400-RX-E4CE02BB0001", "NHD-400-TX-E4CE02AA0001"


def _sources() -> tuple[list[DeviceJsonString], list[DeviceStatus], list[DeviceInfo]]:
    return (
        DeviceJsonString.parse(RAW["config get devicejsonstring"]),
        DeviceStatus.parse(RAW["config get device status"]),
        DeviceInfo.parse(RAW["config get device info"]),
    )


def test_all_sources_merged() -> None:
    """Each endpoint combines its list entry, status and info."""
    transmitters, receivers = build_device_collections(*_sources())

    assert set(receivers) == {RX1, "NHD-400-RX-E4CE02BB0002"}
    assert set(transmitters) == {TX1, "NHD-400-TX-E4CE02AA0002"}
    rx, tx = receivers[RX1], transmitters[TX1]
    assert isinstance(rx, DeviceReceiver) and isinstance(tx, DeviceTransmitter)
    assert (rx.alias_name, rx.mac, rx.version, rx.hdmi_out_frame_rate) == ("Display1", "e4:ce:02:bb:00:01", "v2.5.6", 0)
    assert (tx.alias_name, tx.online, tx.hdmi_in_frame_rate) == ("Source1", True, 60)


def test_devices_without_status_or_info_are_kept() -> None:
    """Devices the controller reports no status/info for (offline) are kept, without that data."""
    json_list, _, _ = _sources()
    transmitters, receivers = build_device_collections(json_list, [], [])

    assert len(transmitters) == len(receivers) == 2
    assert receivers[RX1].mac is None
    assert receivers[RX1].hdmi_out_frame_rate is None


def test_union_of_sources() -> None:
    """A device missing from the device list but present in status/info is still created."""
    json_list, status, info = _sources()
    transmitters, receivers = build_device_collections([d for d in json_list if d.trueName != RX1], status, info)

    rx = receivers[RX1]
    assert (rx.alias_name, rx.online, rx.mac) == ("Display1", True, "e4:ce:02:bb:00:01")
    assert len(transmitters) == 2


def test_status_only_device_type_inferred_from_name() -> None:
    """A device only in status gets its type from its true name and its IP from info; unknown types are skipped."""
    transmitters, receivers = build_device_collections(
        [],
        [
            DeviceStatus(aliasname="Src", name="NHD-400-TX-AA"),
            DeviceStatus(aliasname="X", name="NHD-600-TRX-AA"),
            DeviceStatus(aliasname="Disp", name="NHD-400-RX-BB"),
        ],
        [DeviceInfo(aliasname="Disp", name="NHD-400-RX-BB", ip4addr="192.0.2.5")],
    )

    assert transmitters["NHD-400-TX-AA"].alias_name == "Src"
    assert transmitters["NHD-400-TX-AA"].online is True
    assert receivers["NHD-400-RX-BB"].ip == "192.0.2.5"
    assert len(transmitters) + len(receivers) == 2


def test_device_only_in_cached_info_is_not_present() -> None:
    """Device info is cached, so a device found only there (deleted on the controller) is not created."""
    transmitters, receivers = build_device_collections(
        [], [], [DeviceInfo(aliasname="Disp", name="NHD-400-RX-BB", ip4addr="192.0.2.5")]
    )

    assert transmitters == receivers == {}


def test_invalid_device_type_is_skipped() -> None:
    """A listed device with an unknown type is skipped, the others are kept."""
    json_list, status, info = _sources()
    json_list[0] = replace(json_list[0], deviceType="Gateway")
    transmitters, receivers = build_device_collections(json_list, status, info)

    assert RX1 not in receivers
    assert len(transmitters) == 2


def test_device_without_alias_is_addressed_by_true_name() -> None:
    """The library rejects empty names, so an endpoint with no alias is sent by its true name (hostname)."""
    _, receivers = build_device_collections([], [DeviceStatus(aliasname="", name="NHD-400-RX-BB")], [])

    assert receivers["NHD-400-RX-BB"].api_name == "NHD-400-RX-BB"
