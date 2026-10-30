"""Find the controller's MAC address from its mDNS announcement.

The controller exposes no MAC or serial over the SSH API, but announces itself as
`NHD-000-CTL-e4ce02aabbcc [e4:ce:02:aa:bb:cc]._workstation._tcp.local.`.
"""

from __future__ import annotations

import asyncio
import logging
import re

from zeroconf import DNSIncoming, DNSOutgoing, DNSPointer, DNSQuestion

_LOGGER = logging.getLogger(__name__)

# DNS values (RFC 1035/6762), not imported from zeroconf.const whose names are private.
_CLASS_IN, _FLAGS_QR_QUERY, _MDNS_PORT, _TYPE_PTR = 1, 0, 5353, 12

SERVICE_TYPE = "_workstation._tcp.local."
LOOKUP_TIMEOUT = 1.5  # seconds; a controller on the LAN answers in milliseconds

# The MAC in brackets, or the 12 hex digits after the model name.
_MAC_IN_NAME = re.compile(r"\[((?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2})\]|-([0-9a-f]{12})\b", re.IGNORECASE)


def mac_from_name(name: str) -> str | None:
    """Return the MAC (12 lowercase hex digits) in an mDNS instance name, or None."""
    if not (match := _MAC_IN_NAME.search(name)):
        return None
    return re.sub("[:-]", "", match[1] or match[2]).lower()


def is_mac(value: str | None) -> bool:
    """Return True if `value` is a MAC as stored in unique_id (entries identified by host are not)."""
    return value is not None and re.fullmatch("[0-9a-f]{12}", value) is not None


class _FirstReply(asyncio.DatagramProtocol):
    """Resolve a future with the first datagram received."""

    def __init__(self, reply: asyncio.Future[bytes]) -> None:
        self.reply = reply

    def datagram_received(self, data: bytes, addr: tuple[str | int, ...]) -> None:
        if not self.reply.done():
            self.reply.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self.reply.done():
            self.reply.set_exception(exc)


async def async_lookup_mac(host: str, port: int = _MDNS_PORT) -> str | None:
    """Ask `host` directly (unicast mDNS) for its _workstation._tcp instance and return its MAC, or None.

    The query comes from an ephemeral port, so the controller answers by unicast (RFC 6762 6.7), which
    also works across subnets where multicast discovery does not.
    """
    query = DNSOutgoing(_FLAGS_QR_QUERY, multicast=False)
    query.add_question(DNSQuestion(SERVICE_TYPE, _TYPE_PTR, _CLASS_IN))
    loop = asyncio.get_running_loop()
    reply: asyncio.Future[bytes] = loop.create_future()
    transport: asyncio.DatagramTransport | None = None
    try:
        async with asyncio.timeout(LOOKUP_TIMEOUT):
            transport, _ = await loop.create_datagram_endpoint(lambda: _FirstReply(reply), remote_addr=(host, port))
            transport.sendto(query.packets()[0])
            data = await reply
    except (OSError, TimeoutError) as err:
        _LOGGER.debug("No mDNS reply from %s: %r", host, err)
        return None
    finally:
        if transport:
            transport.close()
    for record in DNSIncoming(data).answers():
        if isinstance(record, DNSPointer) and (mac := mac_from_name(record.alias)):
            return mac
    _LOGGER.debug("mDNS reply from %s has no NetworkHD instance name", host)
    return None
