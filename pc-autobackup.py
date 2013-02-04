#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Main runnable for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import optparse

from twisted.internet import reactor
from twisted.web.server import Site

import common
import ssdp
import mediaserver


def main():
  parser = optparse.OptionParser()
  parser.add_option('-b', '--bind', dest='bind',
                    help='Bind the server to a specific IP',
                    metavar='IPADDRESS')
  parser.add_option('-d', '--debug', dest='debug', action="store_true",
                    default=False, help='Print debug information')
  (options, args) = parser.parse_args()

  config = common.LoadOrCreateConfig()
  if options.bind:
    config.set('AUTOBACKUP', 'default_interface', options.bind)

  #ssdp.StartSSDPServer(debug=options.debug)
  #mediaserver.StartMediaServer(debug=options.debug)
  resource = mediaserver.MediaServer(debug=options.debug)
  factory = Site(resource)
  reactor.listenMulticast(1900, ssdp.SSDPServer(debug=options.debug))
  reactor.listenTCP(52235, factory)
  reactor.run()


if __name__ == '__main__':
  main()
