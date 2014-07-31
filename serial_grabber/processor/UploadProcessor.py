# !/usr/bin/env python
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
import base64

import logging
import socket
import urllib
import time

from serial_grabber.processor import Processor
from urlparse import urlparse


class HTTPBasicAuthentication:
    """
    HTTP Basic Authentication

    :param str username: The username for the HTTP request
    :param str password: The password for the HTTP request
    """

    def __init__(self, username, password):
        self.basic = "Basic %s" % (base64.b64encode("%s:%s" % (username, password)))

    def add_header(self, headers):
        headers["Authorization"] = self.basic


class UploadProcessor(Processor):
    """
    Encodes the data as a HTTP form and uploads it to the configured url.

    :param str url: The url to upload the data to.
    :param int upload_error_sleep: The amount of time to sleep if an error occurred during upload.
    :param auth: The credentials to use.
    :type auth: serial_grabber.processor.UploadProcessor.HTTPBasicAuthentication or None
    :param dict form_params: Addition parameters to be added to the uploaded form.
    :param dict headers: Headers to add to the upload requests.

    """
    logger = logging.getLogger("Uploader")

    def __init__(self, url, upload_error_sleep=10, auth=None, form_params=None, headers=None):
        socket.setdefaulttimeout(15)
        self.url = url
        self.upload_error_sleep = upload_error_sleep
        self.upload_params = None
        if form_params is not None:
            self.upload_params = form_params
        self.headers = [{}, headers][headers is not None]
        if auth is not None:
            auth.add_header(self.headers)


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

        self.headers["Content-type"] = "application/x-www-form-urlencoded"
        self.headers["Accept"] = "text/plain"
        if _url.scheme == "https":
            conn = httplib.HTTPSConnection(_url.hostname)
        else:
            conn = httplib.HTTPConnection(_url.hostname)
        conn.request("POST", _url.path, body=params, headers=self.headers)
        response = conn.getresponse()
        self.logger.info("HTTP Response: %s %s" % (response.status, response.reason))

        data = response.read()
        self.logger.log(5, data)
        conn.close()
        if response.status == 200:
            return True
        else:
            self.logger.error("Upload Error, sleeping for %s seconds" % self.upload_error_sleep)
            time.sleep(self.upload_error_sleep)
            return False
