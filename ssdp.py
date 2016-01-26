#!/usr/bin/env python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple SSDP implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import logging
import re
import socket

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

import common

MSEARCH = re.compile(r'^M-SEARCH \* HTTP/1.1', re.DOTALL)
MSEARCH_DATA = re.compile(r'^([^:]+):\s+(.*)')


class SSDPServer(DatagramProtocol):

  def __init__(self, config_file=None):
    self.logger = logging.getLogger('pc_autobackup.ssdp')
    self.config = common.LoadOrCreateConfig(config_file)

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

      host_ip,host_port = self.GetHostAddress(address)
      self.logger.debug('Received SSDP M-SEARCH on interface %s', host_ip)

      if self.config.has_option('AUTOBACKUP', 'default_interface'):
        if self.config.get('AUTOBACKUP', 'default_interface') != host_ip:
          return

      if msearch_data.get('discovery_type') == 'MediaServer':
        self.SendSSDPResponse(address)

  def GenerateSSDPResponse(self, response_type, ip_address, uuid,
                           notify_fields={}):
    """Generate an SSDP response.

    Args:
      response_type: One of m-search or notify
      ip_address: IP address to use for the response
      uuid: UUID to use for the response
      notify_fields: A dictionary containing NT, NTS, and USN fields

    Returns:
      A string containing an SSDP response
    """
    location = 'LOCATION: http://%s:52235/DMS/SamsungDmsDesc.xml' % ip_address
    if response_type == 'm-search':
      response = ['HTTP/1.1 200 OK',
                  'CACHE-CONTROL: max-age = 1800',
                  'EXT:',
                  location,
                  'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0',
                  'ST: urn:schemas-upnp-org:device:MediaServer:1',
                  'USN: uuid:%s::urn:schemas-upnp-org:device:MediaServer:1' % uuid]
    elif response_type == 'notify':
      response = ['NOTIFY * HTTP/1.1',
                  'HOST: 239.255.255.250:1900',
                  'CACHE-CONTROL: max-age=1800',
                  location,
                  'NT: %s' % notify_fields.get('NT', ''),
                  'NTS: %s' % notify_fields.get('NTS', ''),
                  'USN: %s' % notify_fields.get('USN', ''),
                  'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0']

    response.append('CONTENT-LENGTH: 0')
    response.append('')
    response.append('')
    return '\r\n'.join(response)

  def ParseSSDPDiscovery(self, datagram):
    """Parse an SSDP UDP datagram.

    Args:
      datagram: A string containing an SSDP request data

    Returns:
      A dict containing the parsed data
    """
    parsed_data = {}

    for line in datagram.splitlines():
      if line.startswith('M-SEARCH'):
        continue

      m = MSEARCH_DATA.match(line)
      if m:
        parsed_data[m.group(1)] = m.group(2)

        # ST: urn:schemas-upnp-org:device:MediaServer:1
        if m.group(1) == 'ST':
          if m.group(2).startswith('urn:schemas-upnp-org:device:'):
            parsed_data['discovery_type'] = m.group(2).split(':')[3]

    return parsed_data

  def SendSSDPResponse(self, address):
    """Send a response to an SSDP MediaServer discovery request.

    Args:
      address: A tuple of destination IP (string) and port (int)
    """
    host_ip,host_port = self.GetHostAddress(address)
    response = self.GenerateSSDPResponse('m-search',
                                         host_ip,
                                         self.config.get('AUTOBACKUP', 'uuid'))

    address_info = ':'.join([str(x) for x in address])
    self.logger.info('Sending SSDP response to %s', address_info)
    self.logger.debug('Sending SSDP response to %s: %r', address_info,
                      response)
    self.transport.write(response, address)

  def GetHostAddress(self, address):
    """Get host address used when communicating with given udp address.

    Args:
      address: A tuple of destination IP (string) and port (int)

    Returns:
      A tuple of host IP (string) and port (int)
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(address)
    return s.getsockname()

def StartSSDPServer():
  """Start an SSDP server.

  Used for debugging/testing just an SSDP server.
  """
  logging.info('SSDPServer started')
  reactor.listenMulticast(1900, SSDPServer(), listenMultiple=True)
  reactor.run()


def main():
  logging_options = common.LOG_DEFAULTS
  logging_options['filename'] = 'ssdpserver.log'
  logging_options['level'] = logging.DEBUG
  logging.basicConfig(**logging_options)
  StartSSDPServer()


if __name__ == "__main__":
  main()
