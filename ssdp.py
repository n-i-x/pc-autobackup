#!/usr/bin/env python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple SSDP implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import logging
import re

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

import common

MSEARCH = re.compile(r'^M-SEARCH \* HTTP/1.1', re.DOTALL)
MSEARCH_DATA = re.compile(r'^([^:]+):\s+(.*)')

SSDP_RESPONSE = ('HTTP/1.1 200 OK\r\n'
                 'CACHE-CONTROL: max-age = 1800\r\n'
                 'EXT:\r\n'
                 'LOCATION: http://%s:52235/DMS/SamsungDmsDesc.xml\r\n'
                 'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0\r\n'
                 'ST: urn:schemas-upnp-org:device:MediaServer:1\r\n'
                 'USN: %s::urn:schemas-upnp-org:device:MediaServer:1\r\n')


class SSDPServer(DatagramProtocol):

  def __init__(self):
    self.logger = logging.getLogger('SSDPServer')
    self.config = common.LoadOrCreateConfig()

  def startProtocol(self):
    self.transport.setTTL(5)
    self.transport.joinGroup('239.255.255.250')

  def datagramReceived(self, datagram, address):
    m = MSEARCH.match(datagram)
    if m:
      # TODO(jrebeiro): Verify that MediaServer is the only discovery request
      #                 PCAutoBackup responds to.
      msearch_data = self.ParseSSDPDiscovery(datagram)
      if msearch_data.get('discovery_type'):
        self.logger.debug('Received SSDP M-SEARCH for %s from %s',
                          msearch_data.get('discovery_type'), ':'.join(address))
      else:
        self.logger.debug('Received SSDP M-SEARCH from %s', ':'.join(address))

      if msearch_data.get('discovery_type') == 'MediaServer':
        self.logger.info('Sending SSDP response to %s', ':'.join(address))
        self.SendSSDPResponse(address)

  def ParseSSDPDiscovery(self, datagram):
    parsed_data = {}

    for line in datagram.splitlines():
      if line.startswith('M-SEARCH'):
        continue

      m = MSEARCH_DATA.match(line)
      if m:
        parsed_data[m.group(1)] = m.group(2)

        # ST: urn:schemas-upnp-org:device:MediaServer:1
        if m.group(1) == 'ST':
          parsed_data['discovery_type'] = m.group(2).split(':')[3]

    return parsed_data

  def SendSSDPResponse(self, address):
    """Send a response to an SSDP MediaServer discovery request.

    Args:
      address: A tuple of destination IP and Port as strings
    """
    response = SSDP_RESPONSE % (self.config.get('AUTOBACKUP',
                                                'default_interface'),
                                self.config.get('AUTOBACKUP', 'uuid'))
    self.transport.write(response, address)
    self.logger.debug('Response: %s', response)


def StartSSDPServer():
  logging.info('SSDPServer started')
  reactor.listenMulticast(1900, SSDPServer())
  reactor.run()


def main():
  logging_options = common.LOG_DEFAULTS
  logging_options['filename'] = 'ssdpserver.log'
  logging_options['level'] = logging.DEBUG
  logging.basicConfig(**logging_options)
  StartSSDPServer()


if __name__ == "__main__":
  main()
