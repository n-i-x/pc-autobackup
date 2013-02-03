#!/usr/bin/python
#
# Copyright 2013 Jeff Rebeiro (jeff@rebeiro.net) All rights reserved
# Simple UPNP implementation for PC Autobackup

__author__ = 'jeff@rebeiro.net (Jeff Rebeiro)'

import HTMLParser

import common

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


def main():
  config = common.LoadOrCreateConfig()


if __name__ == "__main__":
  main()