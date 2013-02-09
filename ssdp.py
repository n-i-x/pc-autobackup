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
      address_info = ':'.join([str(x) for x in address])
      if msearch_data.get('discovery_type'):
        self.logger.debug('Received SSDP M-SEARCH for %s from %s',
                          msearch_data.get('discovery_type'), address_info)
      else:
        self.logger.debug('Received SSDP M-SEARCH from %s', address_info)

      if msearch_data.get('discovery_type') == 'MediaServer':
        self.SendSSDPResponse(address)

  def GenerateSSDPResponse(self, response_type, ip_address, uuid,
                           notify_fields=None):
    location = 'LOCATION: http://%s:52235/DMS/SamsungDmsDesc.xml' % ip_address
    if response_type == 'm-search':
      response = ['HTTP/1.1 200 OK',
                  'CACHE-CONTROL: max-age = 1800',
                  'EXT:',
                  location,
                  'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0',
                  'ST: urn:schemas-upnp-org:device:MediaServer:1',
                  'USN: %s::urn:schemas-upnp-org:device:MediaServer:1' % uuid]
    elif response_type == 'notify':
      response = ['NOTIFY * HTTP/1.1',
                  'HOST: 239.255.255.250:1900',
                  'CACHE-CONTROL: max-age=1800',
                  location,
                  'NT: %s' % notify_fields.get('NT', ''),
                  'NTS: %s' % notify_fields.get('NTS', ''),
                  'USN: %s' % notify_fields.get('USN', ''),
                  'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0',
                  'CONTENT-LENGTH: 0']

    response.append('')
    return '\r\n'.join(response)

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
      address: A tuple of destination IP (string) and port (int)
    """
    response = self.GenerateSSDPResponse('m-search',
                                         self.config.get('AUTOBACKUP',
                                                         'default_interface'),
                                         self.config.get('AUTOBACKUP', 'uuid'))

    address_info = ':'.join([str(x) for x in address])
    self.logger.info('Sending SSDP response to %s', address_info)
    self.logger.debug('Response: %r', response)
    self.transport.write(response, address)


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
