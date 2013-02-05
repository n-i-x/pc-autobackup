#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Common functions for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import logging
import os
import socket
import uuid

CONFIG_FILE = os.path.expanduser("~/pc_autobackup.cfg")
LOG_DATE_FMT = '[%m/%d/%Y %I:%M %p]'
LOG_FMT = '%(asctime)s[%(name)s] %(levelname)s:%(message)s'

LOG_DEFAULTS = {'level': logging.WARN,
                'format': LOG_FMT,
                'datefmt': LOG_DATE_FMT}


def LoadOrCreateConfig():
  """Load an existing configuration or create one."""
  config = ConfigParser.RawConfigParser()
  config.read(CONFIG_FILE)

  if not config.has_section('AUTOBACKUP'):
    logging.info('Creating configuration file %s', CONFIG_FILE)
    config.add_section('AUTOBACKUP')
    config.set('AUTOBACKUP', 'backup_dir',
               os.path.expanduser('~/PCAutoBackup'))
    config.set('AUTOBACKUP', 'default_interface',
               socket.gethostbyname(socket.gethostname()))
    config.set('AUTOBACKUP', 'server_name', '[PC]AutoBackup')
    config.set('AUTOBACKUP', 'uuid', uuid.uuid4())
    with open(CONFIG_FILE, 'wb') as config_file:
      config.write(config_file)

  return config
