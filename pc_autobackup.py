#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Main runnable for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import logging
import optparse
import platform
import socket

from twisted.internet import reactor
from twisted.web.server import Site

import common
import ssdp
import mediaserver


def GetSystemInfo():
  logger = logging.getLogger('PCAutoBackup')
  logger.debug('Python Version: %s', platform.python_version())
  logger.debug('System Information (platform): %s', platform.platform())
  logger.debug('System Information (uname): %s', ' '.join(platform.uname()))
  logger.debug('System Information (node): %s', platform.node())
  logger.debug('System Information (hostname): %s', socket.gethostname())

  config = common.LoadOrCreateConfig()
  for section in config.sections():
    for option in config.options(section):
      logger.debug('Config (%s): %s = %s', section, option,
                   config.get(section, option))


def main():
  parser = optparse.OptionParser()
  parser.add_option('-b', '--bind', dest='bind',
                    help='bind the server to a specific IP',
                    metavar='IP')
  parser.add_option('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='debug output')
  parser.add_option('--log_file', dest='log_file', default='backup.log',
                    help='output log to file', metavar='FILE')
  parser.add_option('-o', '--output_dir', dest='output_dir',
                    help='output directory for files', metavar='DIR')
  parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                    default=False, help='verbose output')
  (options, args) = parser.parse_args()

  logging_options = common.LOG_DEFAULTS

  if options.verbose:
    logging_options['level'] = logging.INFO
  if options.debug:
    logging_options['level'] = logging.DEBUG

  logging_options['filename'] = options.log_file

  logging.basicConfig(**logging_options)

  console = logging.StreamHandler()
  console.setLevel(logging_options['level'])
  formatter = logging.Formatter('%(asctime)s %(message)s', common.LOG_DATE_FMT)
  console.setFormatter(formatter)
  logging.getLogger('').addHandler(console)

  config = common.LoadOrCreateConfig()
  if options.bind:
    config.set('AUTOBACKUP', 'default_interface', options.bind)
  if options.output_dir:
    config.set('AUTOBACKUP', 'backup_dir', options.output_dir)

  logger = logging.getLogger('PCAutoBackup')
  logger.info('PCAutoBackup started on %s', config.get('AUTOBACKUP',
                                                        'default_interface'))

  if options.debug:
    GetSystemInfo()

  resource = mediaserver.MediaServer()
  factory = Site(resource)
  reactor.listenMulticast(1900, ssdp.SSDPServer())
  logger.info('SSDPServer started')
  reactor.listenTCP(52235, factory)
  logger.info('MediaServer started')
  reactor.run()


if __name__ == '__main__':
  main()
