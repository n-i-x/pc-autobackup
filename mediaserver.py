#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple UPNP MediaServer implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import HTMLParser

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

import common

CREATE_OBJ = re.compile(r'<u:CreateObject xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">.*<Elements>(.*)</Elements>', re.DOTALL)
CREATE_OBJ_DETAILS = re.compile(r'&lt;dc:title&gt;(.*)&lt;/dc:title&gt;.*protocolInfo="\*:\*:(.*):DLNA.ORG_PN=JPEG_LRG;DLNA.ORG_CI=0"')

X_BACKUP = re.compile(r'<u:X_BACKUP_(\w+) xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">')
X_BACKUP_RESPONSE = '''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_BACKUP_%sResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1"/>
  </s:Body>
</s:Envelope>'''

DMS_DESC = '''<?xml version="1.0"?>
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


class MediaServer(Resource):

  isLeaf = True

  def __init__(self):
    self.config = common.LoadOrCreateConfig()

  def render_GET(self, request):
    if request.path == '/DMS/SamsungDmsDesc.xml':
      return self.GetDMSDescriptionResponse()

  def render_POST(self, request):
    if request.path == '/upnp/control/ContentDirectory1':
      return self.GetContentDirectoryResponse(request.content.read())

  def GetContentDirectoryResponse(self, content):
    if X_BACKUP.search(content):
      action = X_BACKUP.search(content).group(1)
      response = X_BACKUP_RESPONSE % action
      print "Response:"
      print response
    if CREATE_OBJECT.search(content):
      obj_didl = CREATE_OBJ.search(content).group(1)
      obj_details = CREATE_OBJ_DETAILS.search(obj_didl).groups()
      obj_name = obj_details[0]
      obj_type = obj_details[1]

    return response

  def GetDMSDescriptionResponse(self):
    response = DMS_DESC % {'friendly_name': self.config.get('AUTOBACKUP',
                                                            'server_name'),
                           'uuid': self.config.get('AUTOBACKUP', 'uuid')}
    if __name__ == '__main__':
      print "Response:"
      print response

    return response


def StartMediaServer():
  resource = MediaServer()
  factory = Site(resource)
  reactor.listenTCP(52235, factory)
  reactor.run()


def main():
  StartMediaServer()


if __name__ == "__main__":
  main()
