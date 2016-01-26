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
import xml.dom.minidom

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

import common

CREATE_OBJ = '"urn:schemas-upnp-org:service:ContentDirectory:1#CreateObject"'
CREATE_OBJ_DIDL = re.compile(r'<Elements>(?P<didl>.*)</Elements>')
CREATE_OBJ_RESPONSE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:CreateObjectResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
      <ObjectID>%(obj_id)s</ObjectID>
      <Result>%(didl)s</Result>
    </u:CreateObjectResponse>
  </s:Body>
</s:Envelope>'''

CREATE_OBJ_RESPONSE_DIDL = '''<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp='urn:schemas-upnp-org:metadata-1-0/upnp/' xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" xmlns:sec="http://www.sec.co.kr/">
  <item id="%(obj_id)s" parentID="%(parent_id)s" restricted="0" dlna:dlnaManaged="00000004">
    <dc:title></dc:title>
    <res protocolInfo="http-get:*:%(obj_type)s:%(obj_subtype)s;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=00D00000000000000000000000000000" importUri="http://%(interface)s:52235/cd/content?didx=0_id=%(obj_id)s" dlna:resumeUpload="0" dlna:uploadedSize="0" size="%(obj_size)s"></res>
    <upnp:class>%(obj_class)s</upnp:class>
  </item>
</DIDL-Lite>'''

X_BACKUP_DONE = '"urn:schemas-upnp-org:service:ContentDirectory:1#X_BACKUP_DONE"'
X_BACKUP_START = '"urn:schemas-upnp-org:service:ContentDirectory:1#X_BACKUP_START"'

X_BACKUP_RESPONSE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_BACKUP_%sResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1"/>
  </s:Body>
</s:Envelope>'''


class Backup(object):

  backup_objects = {}

  def __init__(self, config_file=None):
    self.logger = logging.getLogger('pc_autobackup.mediaserver.backup')
    self.config = common.LoadOrCreateConfig(config_file)

  def _GenerateObjectID(self, obj_date, length=10):
    """Generate an ObjectID for a new backup item.

    Args:
      obj_date: A string containing the object date
      length: An int containing the length of the object id

    Returns:
      A tuple containing the parent id and the object id
    """
    chars = string.letters + string.digits
    rand_chars = ''.join(random.choice(chars) for i in xrange(length))
    parent_id = 'UP_%s' % obj_date
    obj_id = '%s_%s' % (parent_id, rand_chars)
    return (parent_id, obj_id)

  def CreateObject(self, obj_class, obj_date, obj_name, obj_size, obj_subtype,
                   obj_type):
    """Create a new object.

    Args:
      obj_class: A string containing the objects upnp class
      obj_date: A string containing the objects date
      obj_name: A string containing the objects name
      obj_size: A string containing the objects size
      obj_subtype: A string containing the objects subtype
      obj_type: A string containing the objects type

    Returns:
      A string containing the created object id
    """
    (parent_id, obj_id) = self._GenerateObjectID(obj_date)
    self.logger.debug('Creating Backup Object for %s (type:%s size:%s)',
                      obj_name, obj_type, obj_size)
    self.backup_objects[obj_id] = {'obj_class': obj_class,
                                   'obj_date': obj_date,
                                   'obj_name': obj_name,
                                   'obj_size': obj_size,
                                   'obj_subtype': obj_subtype,
                                   'obj_type': obj_type,
                                   'parent_id': parent_id}
    return obj_id

  def FinishBackup(self):
    pass

  def GetObjectDetails(self, obj_id):
    """Get details about an object.

    Args:
      obj_id: A string containing the object id

    Returns:
      A dict containing the object details or None if the object does not exist
    """
    return self.backup_objects.get(obj_id)

  def StartBackup(self):
    pass

  def WriteObject(self, obj_id, data):
    """Save an object to disk.

    Args:
      obj_id: A string containing the object to write
      data: The data to write to disk
    """
    obj_details = self.GetObjectDetails(obj_id)

    obj_dir = [self.config.get('AUTOBACKUP', 'backup_dir')]

    if self.config.getboolean('AUTOBACKUP', 'create_date_subdir'):
      obj_dir.append(obj_details['obj_date'])

    obj_dir = os.path.join(*obj_dir)

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

  def __init__(self, config_file=None):
    self.logger = logging.getLogger('pc_autobackup.mediaserver')
    self.config = common.LoadOrCreateConfig(config_file)
    self.config_file = config_file

  def render_GET(self, request):
    if request.path != '/favicon.ico':
      self.logger.debug('[%s] GET request for %s', request.getClientIP(),
                        request.path)
      self.logger.debug('Request args for %s from %s: %s', request.path,
                        request.getClientIP(), request.args)
      self.logger.debug('Request headers for %s from %s: %s', request.path,
                        request.getClientIP(), request.args)
      self.logger.debug('Request came on interface %s', request.getHost().host)

    if request.path == '/DMS/SamsungDmsDesc.xml':
      self.logger.info('New connection from %s (%s)', request.getClientIP(),
                       request.getHeader('user-agent'))
      self.clients[request.getClientIP()] = request.getHeader('user-agent')
      response = self.GetDMSDescriptionResponse()
    elif request.path.split('/')[-1] == 'ContentDirectory1.xml':
      with open(os.path.join(common.BASEDIR, 'DMS', 'ContentDirectory1.xml'), 'r') as xml_data:
        response = xml_data.read()
    elif request.path.split('/')[-1] == 'ConnectionManager1.xml':
      with open(os.path.join(common.BASEDIR, 'DMS', 'ConnectionManager1.xml'), 'r') as xml_data:
        response = xml_data.read()
    else:
      self.logger.error('Unhandled GET request from %s: %s',
                        request.getClientIP(), request.path)
      request.setResponseCode(404)
      return ''

    if isinstance(response, unicode):
      response = response.encode('utf-8')

    request.setHeader("Content-Type", "text/xml; charset=utf-8")
    self.logger.debug('Sending response for %s to %s: %s', request.path,
                      request.getClientIP(), response)
    return response

  def render_POST(self, request):
    self.logger.debug('Request args for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)
    self.logger.debug('Request headers for %s from %s: %s', request.path,
                      request.getClientIP(), request.args)
    self.logger.debug('Request came on interface %s', request.getHost().host)

    if request.path == '/cd/content':
      response = self.ReceiveUpload(request)
    elif request.path == '/upnp/control/ContentDirectory1':
      response = self.GetContentDirectoryResponse(request)
    else:
      self.logger.error('Unhandled POST request from %s: %s',
                        request.getClientIP(), request.path)
      request.setResponseCode(404)
      return ''

    if isinstance(response, unicode):
      response = response.encode('utf-8')

    request.setHeader("Content-Type", "text/xml; charset=utf-8")
    self.logger.debug('Sending response for %s to %s: %s', request.path,
                      request.getClientIP(), response)
    return response

  def GetContentDirectoryResponse(self, request):
    """Generate the ContentDirectory response XML.

    Args:
      request: A twisted.web.server.Request

    Returns:
      A string containing the XML contents
      In an error, the HTTP response code is set to 404 and an empty string is
      returned.
    """
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

      m = CREATE_OBJ_DIDL.search(soap_xml)
      if m:
        parsed_data = self.ParseDIDL(m.group('didl'))

        obj_class = parsed_data.get('class')
        obj_date = parsed_data.get('date')
        obj_name = parsed_data.get('name')
        obj_size = parsed_data.get('size')

        try:
          obj_type = parsed_data.get('protocolInfo').split(':')[2]
          obj_subtype = parsed_data.get('protocolInfo').split(':')[3]
        except IndexError:
          self.logger.error('Invalid DIDL: %s', soap_xml)
          request.setResponseCode(404)
          return ''

        backup = Backup(self.config_file)
        obj_id = backup.CreateObject(obj_class, obj_date, obj_name, obj_size,
                                     obj_subtype, obj_type)
        obj_details = backup.GetObjectDetails(obj_id)

        self.logger.info('Ready to receive %s (%s size:%s)', obj_name, obj_type,
                         obj_size)

        response_dict = {
            'interface': request.getHost().host,
            'obj_class': obj_class,
            'obj_id': obj_id,
            'obj_size': obj_size,
            'obj_subtype': obj_subtype,
            'obj_type': obj_type,
            'parent_id': obj_details['parent_id']}

        didl = CREATE_OBJ_RESPONSE_DIDL % response_dict
        response_dict['didl'] = common.EscapeHTML(didl)
        response = CREATE_OBJ_RESPONSE % response_dict
    elif soapaction == X_BACKUP_DONE:
      self.logger.info('Backup complete for %s (%s)', request.getClientIP(),
                       self.clients[request.getClientIP()])
      response = X_BACKUP_RESPONSE % 'DONE'
    else:
      self.logger.error('Unhandled soapaction: %s', soapaction)
      request.setResponseCode(404)
      return ''

    return response

  def GetDMSDescriptionResponse(self):
    """Generate the DMS Description response XML.

    Returns:
      A string containing the XML contents
    """
    with open(os.path.join(common.BASEDIR, 'DMS', 'SamsungDmsDesc.xml'), 'r') as dms_desc:
      response = dms_desc.read() % {
          'friendly_name': self.config.get('AUTOBACKUP', 'server_name'),
          'uuid': self.config.get('AUTOBACKUP', 'uuid')}

    return response

  def ParseDIDL(self, didl):
    """Parse DIDL.

    The following is an example of the DIDL to be parsed:

      <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:dlna = "urn:schemas-dlna-org:metadata-1-0/">
        <item id="" restricted="0" parentID="DLNA.ORG_AnyContainer" >
          <dc:title>SAM_0001.JPG</dc:title>
          <dc:date>2012-01-01</dc:date>
          <upnp:class>object.item.imageItem</upnp:class>
          <res protocolInfo="*:*:image/jpeg:DLNA.ORG_PN=JPEG_LRG;DLNA.ORG_CI=0" size="4429673" ></res>
        </item>
      </DIDL-Lite>

    The example DIDL would return the following dict:

      {'class': 'object.item.imageItem',
       'date': '2012-01-01',
       'name': 'SAM_0001.JPG',
       'protocolInfo': '*:*:image/jpeg:DLNA.ORG_PN=JPEG_LRG;DLNA.ORG_CI=0',
       'size': '4429673'}

    Args:
      didl: A string containing the DIDL to be parsed

    Returns:
      A dict containing the item's elements
    """
    parser = HTMLParser.HTMLParser()
    didl = parser.unescape(didl)

    didl_elements = {}
    dom = xml.dom.minidom.parseString(didl)

    def getText(node):
      rc = []
      for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
          rc.append(child.data)
      return ''.join(rc)

    title = dom.getElementsByTagName('dc:title')
    if title:
      didl_elements['name'] = getText(title[0])

    date = dom.getElementsByTagName('dc:date')
    if date:
      didl_elements['date'] = getText(date[0])

    upnp_class = dom.getElementsByTagName('upnp:class')
    if upnp_class:
      didl_elements['class'] = getText(upnp_class[0])

    res = dom.getElementsByTagName('res')
    if res:
      for k, v in res[0].attributes.items():
        didl_elements[k] = v

    return didl_elements

  def ReceiveUpload(self, request):
    """Receive an uploaded file.

    Args:
      request: A twisted.web.server.Request

    Returns:
      An empty string
    """
    response = ''

    obj_id = request.args['didx'][0].split('=')[1]
    backup = Backup(self.config_file)

    data = request.content.read()
    backup.WriteObject(obj_id, data)

    return response


def StartMediaServer():
  """Start a MediaServer server.

  Used for debugging/testing just a MediaServer server.
  """
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
