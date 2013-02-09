# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Common functions for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import logging
import os
import re
import socket
import uuid

CAMERA_CONFIG = {
  'SAMSUNG WB150': {'desc_file': os.path.join('DLNA_WEB_ROOT',
                                              'SAMSUNGAUTOBACKUPDESC.INI')},
  'SAMSUNG NX1000': {'desc_file': os.path.join('dlna_web_root',
                                               'SAMSUNGAutoBackupDESC.ini')}}
CONFIG_FILE = os.path.expanduser("~/pc_autobackup.cfg")
CAMERA_INFO_FILE = [os.path.join('system', 'device.xml'),
                    os.path.join('SYSTEM', 'DEVICE.XML'),
                    os.path.join('SYSTEM', 'Device.xml')]
CAMERA_MODEL = re.compile(r'<BaseModelName\s*value="(.*)"\s*/>')

DESC_SERVER_NAME = re.compile(r'friendlyName\s*=\s*(.*)')
DESC_UUID = re.compile(r'UDN\s*=\s*uuid:(.*)')

DESC_INI = '''MacAddr=%(mac_address)s
UDN=uuid:%(uuid)s
friendlyName=%(server_name)s
WOLSupport=1
ServerFlag=1
'''

LOG_DATE_FMT = '[%m/%d/%Y %I:%M %p]'
LOG_FMT = '%(asctime)s[%(name)s] %(levelname)s:%(message)s'
LOG_DEFAULTS = {'level': logging.INFO,
                'format': LOG_FMT,
                'datefmt': LOG_DATE_FMT}


def GenerateUUID():
  uuid_prefix = '4a682b0b-0361-dbae-6155'
  uuid_suffix = str(uuid.uuid4()).split('-')[-1]
  return '-'.join([uuid_prefix, uuid_suffix])


def LoadOrCreateConfig():
  """Load an existing configuration or create one."""
  config = ConfigParser.RawConfigParser()
  config.read(CONFIG_FILE)

  if not config.has_section('AUTOBACKUP'):
    logging.info('Creating configuration file %s', CONFIG_FILE)
    config.add_section('AUTOBACKUP')
  if not config.has_option('AUTOBACKUP', 'backup_dir'):
    config.set('AUTOBACKUP', 'backup_dir',
               os.path.expanduser('~/PCAutoBackup'))
  if not config.has_option('AUTOBACKUP', 'default_interface'):
    try:
      config.set('AUTOBACKUP', 'default_interface',
                 socket.gethostbyname(socket.gethostname()))
    except socket.error:
      logging.error('Unable to determine IP address. Please set manually!')
      config.set('AUTOBACKUP', 'default_interface', '127.0.0.1')
  if not config.has_option('AUTOBACKUP', 'server_name'):
    config.set('AUTOBACKUP', 'server_name', '[PC]AutoBackup')
  if not config.has_option('AUTOBACKUP', 'uuid'):
    config.set('AUTOBACKUP', 'uuid', GenerateUUID())

  with open(CONFIG_FILE, 'wb') as config_file:
    config.write(config_file)

  return config
  