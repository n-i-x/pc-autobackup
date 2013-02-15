#!/usr/bin/env python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple UPNP MediaServer implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import HTMLParser
import logging
import os
import random
import re
import string

from twisted.internet import reactor
from twisted.web.error import NoResource
from twisted.web.resource import Resource
from twisted.web.server import Site

import common

CREATE_OBJ = '"urn:schemas-upnp-org:service:ContentDirectory:1#CreateObject"'
CREATE_OBJ_DIDL = re.compile(r'.*<Elements>(?P<didl>.*dc:title&gt;(?P<name>.*)&lt;/dc:title.*dc:date&gt;(?P<date>.*)&lt;/dc:date.*protocolInfo=&quot;\*:\*:(?P<type>.*):DLNA.ORG_PN.*size=&quot;(?P<size>\d+)&quot;.*)</Elements>.*')
CREATE_OBJ_RESPONSE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:CreateObjectResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
      <ObjectID>%(obj_id)s</ObjectID>
      <Result>&lt;DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp='urn:schemas-upnp-org:metadata-1-0/upnp/' xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" xmlns:sec="http://www.sec.co.kr/"&gt;&lt;item id="%(obj_id)s" parentID="%(parent_id)s" restricted="0" dlna:dlnaManaged="00000004"&gt;&lt;dc:title&gt;&lt;/dc:title&gt;&lt;res protocolInfo="http-get:*:%(obj_type)s:DLNA.ORG_PN=JPEG_LRG;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=00D00000000000000000000000000000" importUri="http://%(interface)s:52235/cd/content?didx=0_id=%(obj_id)s" dlna:resumeUpload="0" dlna:uploadedSize="0" size="%(obj_size)s"&gt;&lt;/res&gt;&lt;upnp:class&gt;object.item.imageItem&lt;/upnp:class&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</Result>
    </u:CreateObjectResponse>
  </s:Body>
</s:Envelope>'''

X_BACKUP_DONE = '"urn:schemas-upnp-org:service:ContentDirectory:1#X_BACKUP_DONE"'
X_BACKUP_START = '"urn:schemas-upnp-org:service:ContentDirectory:1#X_BACKUP_START"'

X_BACKUP_RESPONSE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_BACKUP_%sResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1"/>
  </s:Body>
</s:Envelope>'''

DMS_DESC_RESPONSE = '''<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0" xmlns:sec="http://www.sec.co.kr/dlna" xmlns:dlna="urn:schemas-dlna-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <dlna:X_DLNADOC>DMS-1.50</dlna:X_DLNADOC>
    <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
    <friendlyName>%(friendly_name)s</friendlyName>
    <manufacturer>Samsung Electronics</manufacturer>
    <manufacturerURL>http://www.samsung.com</manufacturerURL>
    <modelDescription>Samsung PC AutoBackup</modelDescription>
    <modelName>WiselinkPro</modelName>
    <modelNumber>1.0</modelNumber>
    <modelURL>http://www.samsung.com</modelURL>
    <serialNumber>20080818WiselinkPro</serialNumber>
    <sec:ProductCap>smi,DCM10,getMediaInfo.sec,getCaptionInfo.sec</sec:ProductCap>
    <UDN>uuid:%(uuid)s</UDN>
    <serviceList>
      <service>
        <serviceType>urn:schemas-upnp-org:service:ContentDirectory:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:ContentDirectory</serviceId>
        <controlURL>/upnp/control/ContentDirectory1</controlURL>
        <eventSubURL>/upnp/event/ContentDirectory1</eventSubURL>
        <SCPDURL>ContentDirectory1.xml</SCPDURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:ConnectionManager:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:ConnectionManager</serviceId>
        <controlURL>/upnp/control/ConnectionManager1</controlURL>
        <eventSubURL>/upnp/event/ConnectionManager1</eventSubURL>
        <SCPDURL>ConnectionManager1.xml</SCPDURL>
      </service>
    </serviceList>
  </device>
</root>'''


class Backup(object):

  backup_objects = {}

  def __init__(self):
    self.logger = logging.getLogger('MediaServer.Backup')
    self.config = common.LoadOrCreateConfig()

  def _GenerateObjectID(self, obj_date, length=10):
    chars = string.letters + string.digits
    rand_chars = ''.join(random.choice(chars) for i in xrange(length))
    parent_id = 'UP_%s' % obj_date
    obj_id = '%s_%s' % (parent_id, rand_chars)
    return (parent_id, obj_id)

  def CreateObject(self, obj_name, obj_date, obj_type, obj_size):
    (parent_id, obj_id) = self._GenerateObjectID(obj_date)
    self.logger.debug('Creating Backup Object for %s (type:%s size:%s)',
                      obj_name, obj_type, obj_size)
    self.backup_objects[obj_id] = {'obj_name': obj_name,
                                   'obj_date': obj_date,
                                   'obj_type': obj_type,
                                   'parent_id': parent_id,
                                   'obj_size': obj_size}
    return obj_id

  def FinishBackup(self):
    pass

  def GetObjectDetails(self, obj_id):
    return self.backup_objects.get(obj_id)

  def StartBackup(self):
    pass

  def WriteObject(self, obj_id, data):
    obj_details = self.GetObjectDetails(obj_id)

    obj_dir = os.path.join(self.config.get('AUTOBACKUP', 'backup_dir'),
                           obj_details['obj_date'])

    if not os.path.isdir(obj_dir):
      self.logger.info('Creating output dir %s', obj_dir)
      os.makedirs(obj_dir)

    obj_file = os.path.join(obj_dir, obj_details['obj_name'])

    self.logger.info('Saving %s to %s', obj_details['obj_name'], obj_dir)
    with open(obj_file, 'wb') as f:
      f.write(data)
    self.logger.info('%s saved successfully', obj_details['obj_name'])

    del(self.backup_objects[obj_id])


class MediaServer(Resource):

  clients = {}
  isLeaf = True

  def __init__(self):
    self.logger = logging.getLogger('MediaServer')
    self.config = common.LoadOrCreateConfig()

  def render_GET(self, request):
    self.logger.debug('Request args for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)
    self.logger.debug('Request headers for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)

    if request.path == '/DMS/SamsungDmsDesc.xml':
      self.logger.info('New connection from %s (%s)',
                       request.getClientIP(),
                       request.getHeader('user-agent'))
      self.clients[request.getClientIP()] = request.getHeader('user-agent')
      response = self.GetDMSDescriptionResponse()
    else:
      self.logger.error('Unhandled GET request from %s: %s',
                        request.getClientIP(), request.path)
      return NoResource()

    self.logger.debug('Response: %s', response)
    return response

  def render_POST(self, request):
    self.logger.debug('Request args for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)
    self.logger.debug('Request headers for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)

    if request.path == '/cd/content':
      response = self.ReceiveUpload(request)
    elif request.path == '/upnp/control/ContentDirectory1':
      response = self.GetContentDirectoryResponse(request)
    else:
      self.logger.error('Unhandled POST request from %s: %s',
                        request.getClientIP(), request.path)
      return NoResource()

    self.logger.debug('Sending response for %s to %s: %s', request.path,
                      request.getClientIP(), response)
    return response

  def GetContentDirectoryResponse(self, request):
    self.logger.debug('Request content for %s from %s: %s', request.path,
                      request.getClientIP(), request.content.read())
    request.content.seek(0)

    soapaction = request.getHeader('soapaction')

    if soapaction == X_BACKUP_START:
      self.logger.info('Starting backup for %s (%s)', request.getClientIP(),
                       self.clients[request.getClientIP()])
      response = X_BACKUP_RESPONSE % 'START'
    elif soapaction == CREATE_OBJ:
      soap_xml = request.content.read()

      m = CREATE_OBJ_DIDL.match(soap_xml)
      if m:
        obj_name = m.group('name')
        obj_date = m.group('date')
        obj_type = m.group('type')
        obj_size = m.group('size')

        backup = Backup()
        obj_id = backup.CreateObject(obj_name, obj_date, obj_type, obj_size)
        obj_details = backup.GetObjectDetails(obj_id)

        self.logger.info('Ready to receive %s (%s size:%s)', obj_name, obj_type,
                         obj_size)
        response = CREATE_OBJ_RESPONSE % {
            'interface': self.config.get('AUTOBACKUP', 'default_interface'),
            'obj_id': obj_id,
            'obj_type': obj_type,
            'obj_size': obj_size,
            'parent_id': obj_details['parent_id']}
    elif soapaction == X_BACKUP_DONE:
      self.logger.info('Backup complete for %s (%s)', request.getClientIP(),
                       self.clients[request.getClientIP()])
      response = X_BACKUP_RESPONSE % 'DONE'
    else:
      self.logger.error('Unhandled soapaction: %s', soapaction)
      return NoResource()

    return response

  def GetDMSDescriptionResponse(self):
    response = DMS_DESC_RESPONSE % {
        'friendly_name': self.config.get('AUTOBACKUP', 'server_name'),
        'uuid': self.config.get('AUTOBACKUP', 'uuid')}

    return response

  def ReceiveUpload(self, request):
    response = ''

    obj_id = request.args['didx'][0].split('=')[1]
    backup = Backup()

    data = request.content.read()
    backup.WriteObject(obj_id, data)

    return response


def StartMediaServer():
  logging.info('MediaServer started')
  resource = MediaServer()
  factory = Site(resource)
  reactor.listenTCP(52235, factory)
  reactor.run()


def main():
  logging_options = common.LOG_DEFAULTS
  logging_options['filename'] = 'mediaserver.log'
  logging_options['level'] = logging.DEBUG
  logging.basicConfig(**logging_options)
  StartMediaServer()


if __name__ == '__main__':
  main()
