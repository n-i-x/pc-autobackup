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
  'default': {'desc_file': os.path.join('dlna_web_root',
                                        'samsungautobackupdesc.ini')},
  'SAMSUNG EX2': {'desc_file': os.path.join('dlna_web_root',
                                            'SAMSUNGAutoBackupDESC.ini')},
  'SAMSUNG DV300': {'desc_file': os.path.join('DLNA_WEB_ROOT',
                                              'SAMSUNGAutoBackupDESC.ini')},
  'SAMSUNG WB150': {'desc_file': os.path.join('DLNA_WEB_ROOT',
                                              'SAMSUNGAUTOBACKUPDESC.INI')},
  'SAMSUNG WB350F': {'desc_file': os.path.join('DLNA_WEB_ROOT',
                                              'SAMSUNGAutoBackupDESC.ini')},
  'SAMSUNG NX1000': {'desc_file': os.path.join('dlna_web_root',
                                               'SAMSUNGAutoBackupDESC.ini')},
  'SAMSUNG NX500': {'desc_file': os.path.join('dlna_web_root',
                                               'SAMSUNGAutoBackupDESC.ini')}}

BASEDIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.expanduser("~/.pc_autobackup.cfg")
CAMERA_INFO_FILE = [os.path.join('system', 'device.xml'),
                    os.path.join('SYSTEM', 'DEVICE.XML'),
                    os.path.join('SYSTEM', 'Device.xml'),
                    os.path.join('config', 'RVF', 'xml', 'DeviceDescription.xml')]
CAMERA_MODEL = re.compile(r'<BaseModelName\s*value="(.*)"\s*/>')

DESC_SERVER_NAME = re.compile(r'friendlyName\s*=\s*(.*)')
DESC_UUID = re.compile(r'UDN\s*=\s*uuid:(.*)')

DESC_INI = '''MacAddr=%(mac_address)s\r
UDN=uuid:%(uuid)s\r
friendlyName=%(server_name)s\r
WOLSupport=1\r
ServerFlag=1\r
'''

LOG_DATE_FMT = '[%m/%d/%Y %I:%M %p]'
LOG_FMT = '%(asctime)s %(message)s'
LOG_DEFAULTS = {'level': logging.INFO,
                'format': LOG_FMT,
                'datefmt': LOG_DATE_FMT}


def EscapeHTML(html):
  """Escape characters in the given HTML.

  Args:
    html: A string containing HTML to be escaped

  Returns:
    A string containing escaped HTML
  """
  html_codes = (('&', '&amp;'),
                ('<', '&lt;'),
                ('>', '&gt;'),
                ('"', '&quot;'),
                ("'", '&apos;'))
  for old, new in html_codes:
    html = html.replace(old, new)
  
  return html

def GenerateUUID():
  """Generate a UUID.

  Returns:
    A string containing a valid UUID
  """
  uuid_prefix = '4a682b0b-0361-dbae-6155'
  uuid_suffix = str(uuid.uuid4()).split('-')[-1]
  return '-'.join([uuid_prefix, uuid_suffix])


def LoadOrCreateConfig(config_file=None):
  """Load an existing configuration or create one.

  Returns:
    ConfigParser.RawConfigParser
  """
  if not config_file:
    config_file = CONFIG_FILE

  logger = logging.getLogger('pc_autobackup.common')

  config = ConfigParser.RawConfigParser()
  config.read(config_file)

  if not config.has_section('AUTOBACKUP'):
    logger.info('Creating configuration file %s', config_file)
    config.add_section('AUTOBACKUP')
  if not config.has_option('AUTOBACKUP', 'backup_dir'):
    config.set('AUTOBACKUP', 'backup_dir',
               os.path.expanduser('~/PCAutoBackup'))
  if not config.has_option('AUTOBACKUP', 'create_date_subdir'):
    config.set('AUTOBACKUP', 'create_date_subdir', '1')
  if not config.has_option('AUTOBACKUP', 'server_name'):
    config.set('AUTOBACKUP', 'server_name', '[PC]AutoBackup')
  if not config.has_option('AUTOBACKUP', 'uuid'):
    config.set('AUTOBACKUP', 'uuid', GenerateUUID())

  with open(config_file, 'wb') as file:
    config.write(file)

  return config
  
