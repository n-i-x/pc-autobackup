#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jrebeiro@gmail.com) All rights reserved
# Simple SSDP Server for PC Autobackup

__author__ = 'jrebeiro@gmail.com (Jeff Rebeiro)'

import re
import socket
import sys
import uuid
from twisted.internet import reactor
from twisted.internet import task
from twisted.internet.protocol import DatagramProtocol

pattern = r'^M-SEARCH.*HOST: (.*):(\d+).*urn:schemas-upnp-org:device:(\w+):1.*'
MSEARCH = re.compile(pattern, re.DOTALL)

SSDP_RESPONSE = ('HTTP/1.1 200 OK\r\n'
                 'CACHE-CONTROL: max-age = 1800\r\n'
                 'EXT:\r\n'
                 'LOCATION: http://%s:52235/DMS/SamsungDmsDesc.xml\r\n'
                 'SERVER: MS-Windows/XP UPnP/1.0 PROTOTYPE/1.0\r\n'
                 'ST: urn:schemas-upnp-org:device:MediaServer:1\r\n'
                 'USN: %s::urn:schemas-upnp-org:device:MediaServer:1\r\n')

UUID = uuid.uuid4()

class SSDP(DatagramProtocol):

  def __init__(self, ip_address):
    self.ip_address = ip_address
    self.ssdp_address = '239.255.255.250'
    self.ssdp_port = 1900
    self.server = reactor.listenMulticast(self.ssdp_port, self,
                                          listenMultiple=True)
    self.server.setLoopbackMode(1)
    self.server.joinGroup(self.ssdp_address, interface=ip_address)

  def datagramReceived(self, datagram, address):
    m = MSEARCH.match(datagram)
    if m:
      print 'Received M-SEARCH for %s from %r' % (m.group(3), address)
      if m.group(3) == 'MediaServer':
        self.SendSSDPResponse(address)

  def SendSSDPResponse(self, address):
    print "Response:"
    print SSDP_RESPONSE % (address[0], UUID)

  def stop(self):
    self.server.leaveGroup(self.ssdp_address, interface=self.ip_address)
    self.server.stopListening()


def SSDPReactor(ip_address):
  ssdp_server = SSDP(ip_address)
  reactor.addSystemEventTrigger('before', 'shutdown', ssdp_server.stop)


def main():
  ip_address = socket.gethostbyname(socket.gethostname())
  reactor.callWhenRunning(SSDPReactor, ip_address)
  reactor.run()


if __name__ == "__main__":
  main()
