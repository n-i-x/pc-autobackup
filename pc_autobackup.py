#!/usr/bin/env python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Main runnable for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import logging
import optparse
import os
import platform
import re
import socket
import sys
import uuid

from twisted.internet import reactor
from twisted.web.server import Site

import common
import ssdp
import mediaserver


def GetSystemInfo():
  logger = logging.getLogger('PCAutoBackup')
  logger.debug('Command-line: %s', ' '.join(sys.argv))
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


def UpdateCameraConfig(mountpoint, create_desc_file=False):
  logger = logging.getLogger('PCAutoBackup')
  mac_address = hex(uuid.getnode())
  mac_address = re.findall('..', mac_address)
  mac_address = ':'.join(mac_address[1:]).upper()

  desc_file = os.path.join(mountpoint, common.DESC_FILE)

  if create_desc_file:
    with open(desc_file, 'w+') as f:
      logging.info('Creating %s', desc_file)

  if os.path.isfile(desc_file):
    with open(desc_file, 'wb') as f:
      config = common.LoadOrCreateConfig()
      ini_params = {'mac_address': mac_address,
                    'server_name': config.get('AUTOBACKUP', 'server_name'),
                    'uuid': config.get('AUTOBACKUP', 'uuid')}
      try:
        f.write(common.DESC_INI % ini_params)
        logger.info('Configuration saved successfully')
      except IOError as e:
        logger.error('Unable to save configuration: %s', str(e))
  else:
    logger.error('Camera configuration %s does not exist!', desc_file)


def main():
  parser = optparse.OptionParser()
  parser.add_option('-b', '--bind', dest='bind',
                    help='bind the server to a specific IP',
                    metavar='IP')
  parser.add_option('--create_camera_config', dest='create_camera_config',
                    help='create new camera configuration file',
                    metavar='MOUNTPOINT')
  parser.add_option('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='enable debug logging to file')
  parser.add_option('--log_file', dest='log_file', default='backup.log',
                    help='change output log file (default: backup.log)',
                    metavar='FILE')
  parser.add_option('-n', '--name', dest='server_name',
                    help='change server name', metavar='NAME')
  parser.add_option('-o', '--output_dir', dest='output_dir',
                    help='output directory for files', metavar='DIR')
  parser.add_option('-q', '--quiet', dest='quiet', action='store_true',
                    default=False, help='only log errors to console')
  parser.add_option('--update_camera', dest='update_camera',
                    help='update camera with this servers configuration',
                    metavar='MOUNTPOINT')
  (options, args) = parser.parse_args()

  console_logging_options = common.LOG_DEFAULTS.copy()
  logging_options = common.LOG_DEFAULTS.copy()

  if options.quiet:
    console_logging_options['level'] = logging.WARN
  if options.debug:
    logging_options['level'] = logging.DEBUG

  logging_options['filename'] = options.log_file

  logging.basicConfig(**logging_options)

  console = logging.StreamHandler()
  console.setLevel(console_logging_options['level'])
  formatter = logging.Formatter('%(asctime)s %(message)s', common.LOG_DATE_FMT)
  console.setFormatter(formatter)
  logging.getLogger('').addHandler(console)

  config = common.LoadOrCreateConfig()
  update_config = False

  if options.bind:
    config.set('AUTOBACKUP', 'default_interface', options.bind)
    update_config = True
  if options.output_dir:
    config.set('AUTOBACKUP', 'backup_dir', options.output_dir)
    update_config = True
  if options.server_name:
    config.set('AUTOBACKUP', 'server_name', options.server_name)
    update_config = True

  if update_config:
    with open(common.CONFIG_FILE, 'wb') as config_file:
      config.write(config_file)

  if options.create_camera_config:
    UpdateCameraConfig(options.create_camera_config, create_desc_file=True)
    sys.exit(0)

  if options.update_camera:
    UpdateCameraConfig(options.update_camera)
    sys.exit(0)

  logger = logging.getLogger('PCAutoBackup')
  logger.info('PCAutoBackup started on %s', config.get('AUTOBACKUP',
                                                       'default_interface'))
  logger.info('Server name: %s', config.get('AUTOBACKUP', 'server_name'))

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
