#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple SSDP implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import re

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

import common

pattern = r'^M-SEARCH.*HOST: (.*):(\d+).*urn:schemas-upnp-org:device:(\w+):1.*'
MSEARCH = re.compile(pattern, re.DOTALL)

SSDP_RESPONSE = ('HTTP/1.1 200 OK\r\n'
                 'CACHE-CONTROL: max-age = 1800\r\n'
                 'EXT:\r\n'
                 'LOCATION: http://%s:52235/DMS/SamsungDmsDesc.xml\r\n'
                 'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0\r\n'
                 'ST: urn:schemas-upnp-org:device:MediaServer:1\r\n'
                 'USN: %s::urn:schemas-upnp-org:device:MediaServer:1\r\n')


class SSDPServer(DatagramProtocol):

  def __init__(self):
    self.config = common.LoadOrCreateConfig()

  def startProtocol(self):
    self.transport.setTTL(5)
    self.transport.joinGroup('239.255.255.250')

  def datagramReceived(self, datagram, address):
    m = MSEARCH.match(datagram)
    if m:
      # TODO(jrebeiro): Make this print in debug mode when the main runnable
      #                 module is created and implements optparse
      # TODO(jrebeiro): Verify that MediaServer is the only discovery request
      #                 PCAutoBackup responds to.
      print 'Received M-SEARCH for %s from %r' % (m.group(3), address)
      if m.group(3) == 'MediaServer':
        self.SendSSDPResponse(address)

  def SendSSDPResponse(self, address):
    """Send a response to an SSDP MediaServer discovery request.

    Args:
      address: A tuple of destination IP and Port as strings
    """
    response = SSDP_RESPONSE % (self.config.get('AUTOBACKUP',
                                                'default_interface'),
                                self.config.get('AUTOBACKUP', 'uuid'))
    self.transport.write(response, address)
    if __name__ == '__main__':
      print "Response:"
      print response


def StartSSDPServer():
  reactor.listenMulticast(1900, SSDPServer())
  reactor.run()


def main():
  StartSSDPServer()


if __name__ == "__main__":
  main()
