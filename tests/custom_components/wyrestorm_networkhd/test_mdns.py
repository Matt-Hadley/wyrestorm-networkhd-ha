"""Tests for the unicast mDNS MAC lookup, against a local UDP responder."""

import asyncio
from collections.abc import AsyncGenerator, Callable
from unittest.mock import patch

import pytest
from zeroconf import DNSIncoming, DNSOutgoing, DNSPointer
from zeroconf.const import _CLASS_IN, _FLAGS_AA, _FLAGS_QR_RESPONSE, _TYPE_PTR

from custom_components.wyrestorm_networkhd import mdns

from .conftest import MAC

INSTANCE = "NHD-000-CTL-E4CE02AABBCC [e4:ce:02:aa:bb:cc]._workstation._tcp.local."


@pytest.mark.parametrize(
    ("name", "mac"),
    [
        (INSTANCE, MAC),
        ("NHD-CTL-PRO-E4CE02AABBCC._workstation._tcp.local.", MAC),  # no brackets: the hex suffix
        ("nhd-000-ctl [E4-CE-02-AA-BB-CC]._workstation._tcp.local.", MAC),
        ("NHD-000-CTL._workstation._tcp.local.", None),
    ],
)
def test_mac_from_name(name: str, mac: str | None) -> None:
    """The MAC comes from the brackets or the 12 hex digits after the model, normalized."""
    assert mdns.mac_from_name(name) == mac


def test_is_mac() -> None:
    """Only 12 lowercase hex digits count as a MAC unique id."""
    assert mdns.is_mac(MAC)
    assert not mdns.is_mac("192.0.2.10")
    assert not mdns.is_mac(None)


def _reply(*aliases: str) -> bytes:
    out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA, multicast=False)
    for alias in aliases:
        out.add_answer_at_time(DNSPointer(mdns.SERVICE_TYPE, _TYPE_PTR, _CLASS_IN, 120, alias), 0)
    return out.packets()[0]


class _Responder(asyncio.DatagramProtocol):
    def __init__(self, answer: Callable[[bytes], bytes | None]) -> None:
        self.answer = answer
        self.queries: list[DNSIncoming] = []

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        self.queries.append(DNSIncoming(data))
        if (reply := self.answer(data)) is not None:
            self.transport.sendto(reply, addr)


@pytest.fixture
async def responder(socket_enabled: None) -> AsyncGenerator[tuple[_Responder, int]]:
    """A UDP server on 127.0.0.1 that answers with `responder.answer(query)` (None = no reply)."""
    protocol = _Responder(lambda _: _reply(INSTANCE))
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: protocol, local_addr=("127.0.0.1", 0)
    )
    yield protocol, transport.get_extra_info("sockname")[1]
    transport.close()


async def test_lookup_returns_mac(responder: tuple[_Responder, int]) -> None:
    """A PTR query for _workstation._tcp is sent; the MAC comes from the instance name in the answer."""
    protocol, port = responder
    assert await mdns.async_lookup_mac("127.0.0.1", port) == MAC
    [question] = protocol.queries[0].questions
    assert (question.name, question.type) == (mdns.SERVICE_TYPE, _TYPE_PTR)


async def test_lookup_skips_other_names(responder: tuple[_Responder, int]) -> None:
    """Answers without a MAC in the name are ignored."""
    protocol, port = responder
    protocol.answer = lambda _: _reply("printer._workstation._tcp.local.", INSTANCE)
    assert await mdns.async_lookup_mac("127.0.0.1", port) == MAC
    protocol.answer = lambda _: _reply("printer._workstation._tcp.local.")
    assert await mdns.async_lookup_mac("127.0.0.1", port) is None


async def test_lookup_no_reply(responder: tuple[_Responder, int]) -> None:
    """No answer within the timeout gives None."""
    protocol, port = responder
    protocol.answer = lambda _: None
    with patch.object(mdns, "LOOKUP_TIMEOUT", 0.05):
        assert await mdns.async_lookup_mac("127.0.0.1", port) is None


async def test_lookup_socket_error(socket_enabled: None) -> None:
    """A socket error (like ICMP port unreachable, or a name that does not resolve) gives None."""
    loop = asyncio.get_running_loop()
    with patch.object(loop, "create_datagram_endpoint", side_effect=OSError("unreachable")):
        assert await mdns.async_lookup_mac("127.0.0.1") is None


def test_error_received_fails_the_lookup() -> None:
    """An ICMP error reported on the socket ends the wait (once)."""
    loop = asyncio.new_event_loop()
    try:
        reply = loop.create_future()
        protocol = mdns._FirstReply(reply)
        protocol.error_received(ConnectionRefusedError())
        protocol.error_received(ConnectionRefusedError())
        protocol.datagram_received(b"late", ("127.0.0.1", 5353))
        assert isinstance(reply.exception(), ConnectionRefusedError)
    finally:
        loop.close()
