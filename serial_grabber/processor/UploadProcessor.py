#!/usr/bin/env python
# SerialGrabber reads data from a serial port and processes it with the
# configured processor.
# Copyright (C) 2012  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import httplib

import logging
import socket
import urllib

from serial_grabber.processor import Processor
from urlparse import urlparse


class UploadProcessor(Processor):
    logger = logging.getLogger("Uploader")

    def __init__(self, url, **kwargs):
        socket.setdefaulttimeout(15)
        self.url = url
	self.upload_params = None
        if 'params' in kwargs:
            self.upload_params = kwargs['params']

    def process(self, process_entry):
        toRet = False
        _url = urlparse(self.url)
        data = {}
	if self.upload_params is not None: 
            for i in self.upload_params:
                data[i] = self.upload_params[i]

        for i in process_entry.data.config_delegate:
            data[i] = process_entry.data.config_delegate[i]

        params = urllib.urlencode(data)

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        if _url.scheme == "https":
            conn = httplib.HTTPSConnection(_url.hostname)
        else:
            conn = httplib.HTTPConnection(_url.hostname)
        conn.request("POST", _url.path, body=params, headers=headers)
        response = conn.getresponse()
        self.logger.info("HTTP Response: %s %s"%(response.status, response.reason))

        data = response.read()
        self.logger.log(5,data)
        conn.close()
        if response.status == 200:
            return True
        else:
	    return False
        raise Exception(self.url, response.status, response.reason)
