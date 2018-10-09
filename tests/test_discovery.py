# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import socket
import select

from mock import patch, MagicMock as Mock, PropertyMock, call

from pysonos import discover
from pysonos import config
from pysonos.discovery import any_soco, by_name

IP_ADDR = '192.168.1.101'
TIMEOUT = 5

class MockAddress:
    def __init__(self, ip):
        self._ip = ip

    @property
    def ip(self):
        return self._ip

    @property
    def is_IPv4(self):
        return not isinstance(self._ip, tuple)

class MockAdapter:
    def __init__(self, ips):
        self._ips = [MockAddress(x) for x in ips]

    @property
    def ips(self):
        return self._ips

class TestDiscover:
    def test_discover(self, monkeypatch):
        # Create a fake socket, whose data is always a certain string
        monkeypatch.setattr('socket.socket', Mock())
        sock = socket.socket.return_value
        sock.recvfrom.return_value = (
            b'SERVER: Linux UPnP/1.0 Sonos/26.1-76230 (ZPS3)', [IP_ADDR]
        )  # (data, # address)
        monkeypatch.setattr('ifaddr.get_adapters',
            Mock(side_effect=lambda: [
                MockAdapter(['192.168.1.15']),
                MockAdapter(['192.168.1.16'])]))
        # prevent creation of soco instances
        monkeypatch.setattr('pysonos.config.SOCO_CLASS', Mock())
        # Fake return value for select
        monkeypatch.setattr(
            'select.select', Mock(return_value = ([sock], 1, 1)))

        # set timeout
        TIMEOUT = 2
        discover(timeout=TIMEOUT)
        # 9 packets in total should be sent (3 to default, 3 to
        # 192.168.1.15 and 3 to 192.168.1.16)
        assert sock.sendto.call_count == 9
        # select called with the relevant timeout
        select.select.assert_called_with(
            [sock, sock, sock], [], [], min(TIMEOUT, 0.1))
        # SoCo should be created with the IP address received
        config.SOCO_CLASS.assert_called_with(IP_ADDR)

        # Now test include_visible parameter. include_invisible=True should
        # result in calling SoCo.all_zones etc
        # Reset interfaces to always return the same values
        monkeypatch.setattr('ifaddr.get_adapters',
            Mock(side_effect=lambda: [MockAdapter('192.168.1.19')]))
        config.SOCO_CLASS.return_value = Mock(
            all_zones='ALL', visible_zones='VISIBLE')
        assert discover(include_invisible=True) == 'ALL'
        assert discover(include_invisible=False) == 'VISIBLE'

        # if select does not return within timeout SoCo should not be called
        # at all
        # simulate no data being returned within timeout
        select.select.return_value = (0, 1, 1)
        discover(timeout=1)
        # Check no SoCo instance created
        config.SOCO_CLASS.assert_not_called


def test_by_name():
    """Test the by_name method"""
    devices = set()
    for name in ("fake", "non", "Kitchen"):
        mymock = Mock(player_name=name)
        devices.add(mymock)

    # The mock we want to find is the last one
    mock_to_be_found = mymock

    # Patch out discover and test
    with patch("pysonos.discovery.discover") as discover_:
        discover_.return_value = devices

        # Test not found
        device = by_name("Living Room")
        assert device is None
        discover_.assert_called_once_with()

        # Test found
        device = by_name("Kitchen")
        assert device is mock_to_be_found
        discover_.assert_has_calls([call(), call()])
