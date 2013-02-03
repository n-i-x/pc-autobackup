#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple SSDP implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import os
import re
import socket
import sys
import uuid

from twisted.internet import reactor
from twisted.internet import task
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


class SSDP(DatagramProtocol):

  def __init__(self):
    self.config = LoadOrCreateConfig()
    self.ssdp_address = '239.255.255.250'
    self.ssdp_port = 1900
    self.server = reactor.listenMulticast(self.ssdp_port, self,
                                          listenMultiple=True)
    self.server.setLoopbackMode(1)
    self.server.joinGroup(self.ssdp_address,
                          interface=self.config.get('AUTOBACKUP',
                                                    'default_interface'))

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
    # TODO(jrebeiro): Make this send a UDP response once the HTTP server is
    #                 ready.
    print "Response:"
    print SSDP_RESPONSE % (address[0], self.config.get('AUTOBACKUP', 'uuid'))

  def stop(self):
    self.server.leaveGroup(self.ssdp_address,
                           interface=self.config.get('AUTOBACKUP',
                                                     'default_interface'))
    self.server.stopListening()


def SSDPReactor():
  """Callback function for twisted.internet.reactor."""
  ssdp_server = SSDP()
  reactor.addSystemEventTrigger('before', 'shutdown', ssdp_server.stop)


def main():
  config = common.LoadOrCreateConfig()
  reactor.callWhenRunning(SSDPReactor)
  reactor.run()


if __name__ == "__main__":
  main()
