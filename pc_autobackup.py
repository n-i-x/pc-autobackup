#!/usr/bin/env python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Main runnable for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import logging
from logging.handlers import TimedRotatingFileHandler
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


def GetCameraConfig(mountpoint):
  """Get configuration options for a camera.

  Args:
    mountpoint: A string containing the path to the cameras SD card

  Returns:
    A dict containing the cameras config
  """
  logger = logging.getLogger('pc_autobackup')

  device_file = None
  for f in common.CAMERA_INFO_FILE:
    if os.path.isfile(os.path.join(mountpoint, f)):
      device_file = os.path.join(mountpoint, f)
      break

  if device_file:
    if os.path.isfile(device_file):
      with open(device_file, 'r') as f:
        device_xml = f.read()
        m = common.CAMERA_MODEL.search(device_xml)
        if m:
          camera_config = common.CAMERA_CONFIG.get(
              m.group(1), common.CAMERA_CONFIG['default'])
          return camera_config

  logger.error('Unable to determine camera model')
  sys.exit(1)


def GetSystemInfo():
  """Log basic system information to the debug logger."""
  logger = logging.getLogger('pc_autobackup')
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


def ImportCameraConfig(mountpoint):
  """Import the PC AutoBackup settings from a camera.

  Args:
    mountpoint: A string containing the path to the cameras SD card
  """
  logger = logging.getLogger('pc_autobackup')

  camera_config = GetCameraConfig(mountpoint)
  desc_file = os.path.join(mountpoint, camera_config['desc_file'])

  if os.path.isfile(desc_file):
    with open(desc_file, 'r') as f:
      desc_data = f.read()
      logger.info('Loading configuration from camera')
      config = common.LoadOrCreateConfig()

      m = common.DESC_SERVER_NAME.search(desc_data)
      if m:
        friendly_name = m.group(1)
      else:
        logger.error('Unable to determine server name from camera config')
        sys.exit(1)

      m = common.DESC_UUID.search(desc_data)
      if m:
        uuid = m.group(1)
      else:
        logger.error('Unable to determine server name from camera config')
        sys.exit(1)

      config.set('AUTOBACKUP', 'server_name', friendly_name)
      config.set('AUTOBACKUP', 'uuid', uuid)
      with open(common.CONFIG_FILE, 'wb') as config_file:
        logger.info('Saving server configuration')
        try:
          config.write(config_file)
          logger.info('Configuration saved successfully')
        except IOError as e:
          logger.error('Unable to save configuration: %s', str(e))
          sys.exit(1)
      logger.info('Updating camera configuration')
      UpdateCameraConfig(mountpoint)
      logger.info('IMPORTANT: Disable PC AutoBackup on your Windows server!')
  else:
    logger.error('Camera configuration %s does not exist!', desc_file)
    sys.exit(1)


def UpdateCameraConfig(mountpoint, create_desc_file=False):
  """Update the PC AutoBackup settings on a camera.

  Args:
    mountpoint: A string containing the path to the cameras SD card
    create_desc_file: True if the settings file should be created
  """
  logger = logging.getLogger('pc_autobackup')

  mac_address = hex(uuid.getnode())
  mac_address = re.findall('..', mac_address)
  mac_address = ':'.join(mac_address[1:]).upper()

  camera_config = GetCameraConfig(mountpoint)
  desc_file = os.path.join(mountpoint, camera_config['desc_file'])

  if create_desc_file:
    with open(desc_file, 'w+') as f:
      logger.info('Creating %s', desc_file)

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
  parser.add_option('--import_camera_config', dest='import_camera_config',
                    help='update server with cameras configuration',
                    metavar='MOUNTPOINT')
  parser.add_option('--log_file', dest='log_file', default='autobackup.log',
                    help='change output log file (default: autobackup.log)',
                    metavar='FILE')
  parser.add_option('-n', '--name', dest='server_name',
                    help='change server name', metavar='NAME')
  parser.add_option('--no_create_date_subdir', dest='no_create_date_subdir',
                    action='store_true', default=False,
                    help='do not create subdirs in ouput_dir for media dates')
  parser.add_option('-o', '--output_dir', dest='output_dir',
                    help='output directory for files', metavar='DIR')
  parser.add_option('-q', '--quiet', dest='quiet', action='store_true',
                    default=False, help='only log errors to console')
  parser.add_option('--update_camera_config', dest='update_camera_config',
                    help='update camera with this servers configuration',
                    metavar='MOUNTPOINT')
  (options, args) = parser.parse_args()

  log_opts = common.LOG_DEFAULTS.copy()
  lf_log_opts = common.LOG_DEFAULTS.copy()

  if options.quiet:
    log_opts['level'] = logging.WARN
  if options.debug:
    print 'enabling debug'
    lf_log_opts['level'] = logging.DEBUG

  logger = logging.getLogger('pc_autobackup')
  logger.setLevel(logging.DEBUG)

  lf_handler = TimedRotatingFileHandler(options.log_file,
                                        when="midnight",
                                        backupCount=3)
  lf_handler.setLevel(lf_log_opts['level'])
  lf_log_opts['format'] = '%(asctime)s[%(name)s] %(levelname)s:%(message)s'
  formatter = logging.Formatter(lf_log_opts['format'],
                                lf_log_opts['datefmt'])
  lf_handler.setFormatter(formatter)
  logger.addHandler(lf_handler)

  console = logging.StreamHandler()
  console.setLevel(log_opts['level'])
  formatter = logging.Formatter(log_opts['format'],
                                log_opts['datefmt'])
  console.setFormatter(formatter)
  logger.addHandler(console)

  config = common.LoadOrCreateConfig()
  update_config = False

  if options.bind:
    config.set('AUTOBACKUP', 'default_interface', options.bind)
    update_config = True
  if options.no_create_date_subdir:
    config.set('AUTOBACKUP', 'create_date_subdir', '0')
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

  if options.import_camera_config:
    ImportCameraConfig(options.import_camera_config)
    sys.exit(0)

  if options.update_camera_config:
    UpdateCameraConfig(options.update_camera_config)
    sys.exit(0)

  if config.has_option('AUTOBACKUP', 'default_interface'):
    interface = config.get('AUTOBACKUP', 'default_interface')
    logger.info('PCAutoBackup started on %s', interface)
  else:
    interface = ""
    logger.info('PCAutoBackup started on all interfaces')

  logger.info('Server name: %s', config.get('AUTOBACKUP', 'server_name'))

  if options.debug:
    GetSystemInfo()

  reactor.listenMulticast(1900, ssdp.SSDPServer(), listenMultiple=True)
  logger.info('SSDPServer started')

  resource = mediaserver.MediaServer()
  factory = Site(resource)
  reactor.listenTCP(52235, factory, interface=interface)
  logger.info('MediaServer started')

  reactor.run()


if __name__ == '__main__':
  main()
