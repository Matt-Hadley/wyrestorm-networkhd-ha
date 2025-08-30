"""Data models for WyreStorm NetworkHD Integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wyrestorm_networkhd.models.api_query import IpSetting, Version


@dataclass
class DeviceController:
    """Model representing the physical WyreStorm NetworkHD Controller hardware.

    This represents the actual controller device - the physical hardware box that
    manages the matrix switching system. Contains device properties.
    """

    # Version attributes
    api_version: str
    web_version: str
    core_version: str

    # IP Setting attributes
    ip4addr: str
    netmask: str
    gateway: str

    def __post_init__(self):
        self.manufacturer: str = "WyreStorm"
        self.model: str = "NetworkHD Controller"

    # Factory methods
    @classmethod
    def from_wyrestorm_models(cls, version: Version, ip_setting: IpSetting) -> DeviceController:
        """Create a DeviceController from wyrestorm-networkhd Version and IpSetting models.

        Args:
            version: Version model from wyrestorm-networkhd package
            ip_setting: IpSetting model from wyrestorm-networkhd package

        Returns:
            DeviceController instance
        """
        return cls(
            api_version=version.api_version,
            web_version=version.web_version,
            core_version=version.core_version,
            ip4addr=ip_setting.ip4addr,
            netmask=ip_setting.netmask,
            gateway=ip_setting.gateway,
        )

    # Display methods
    def get_device_display_name(self) -> str:
        """Get the display name for the device."""
        return f"Controller - {self.ip4addr}"
