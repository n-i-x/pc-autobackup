#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Common functions for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import ConfigParser
import os
import socket
import uuid

# TODO(jrebeiro): Move the CONFIG_FILE variable to the main runnable module
CONFIG_FILE = os.path.expanduser("~/pc-autobackup.cfg")


def LoadOrCreateConfig():
  """Load an existing configuration or create one."""
  config = ConfigParser.RawConfigParser()
  # TODO(jrebeiro): Move the CONFIG_FILE variable to the main runnable module
  config.read(CONFIG_FILE)

  if not config.has_section('AUTOBACKUP'):
    config.add_section('AUTOBACKUP')
    config.set('AUTOBACKUP', 'uuid', uuid.uuid4())
    config.set('AUTOBACKUP', 'default_interface',
               socket.gethostbyname(socket.gethostname()))
    config.set('AUTOBACKUP', 'server_name', '[PC]AutoBackup')
    with open(CONFIG_FILE, 'wb') as config_file:
      config.write(config_file)

  return config