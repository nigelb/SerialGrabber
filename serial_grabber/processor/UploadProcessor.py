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

import logging
import socket
import time
import requests
from serial_grabber import constants
from serial_grabber.poster_exceptions import BadDataException

from serial_grabber.processor import Processor
from urlparse import urlparse


class UploadProcessor(Processor):
    """
    Encodes the data as a HTTP form and uploads it to the configured url.

    :param str url: The url to upload the data to.
    :param int upload_error_sleep: The amount of time to sleep if an error occurred during upload.
    :param auth: The credentials to use.
    :type auth: serial_grabber.processor.UploadProcessor.HTTPBasicAuthentication or None
    :param dict form_params: Addition parameters to be added to the uploaded form.
    :param dict headers: Headers to add to the upload requests.
    :param dict request_kw: Parameters that are passed to the requests.post method call
    :param dict success_http_code: A list of HTTP status codes indicating that the server accepted the data,
                this data will be moved into the archive.
    :param dict reject_http_code: A list of HTTP status codes indicating that the server rejected the data,
                this data will be moved into the bad data archive.
    :param dict format_url: If True then in the processing method the url will be set to: ``url.format(**process_entry[constants.url_parameters])`` which should be set by your transform.

    """
    logger = logging.getLogger("Uploader")

    def __init__(self, url, upload_error_sleep=10, auth=None, form_params=None, headers=None, request_kw=None,
                 success_http_codes=[200], reject_http_codes=[406], format_url=False):
        socket.setdefaulttimeout(15)
        self.url = url
        self.upload_error_sleep = upload_error_sleep
        self.upload_params = form_params
        self.headers = [{}, headers][headers is not None]
        self.auth = auth
        self.request_kw = [{}, request_kw][request_kw is not None]
        self.success_http_codes = success_http_codes
        self.reject_http_codes = reject_http_codes
        self.format_url = format_url

    def process(self, process_entry):
        if constants.multiple_uploads in process_entry and process_entry[constants.multiple_uploads]:
            data = process_entry[constants.data]
            payloads = process_entry[constants.data][constants.payload]

            for entry in payloads:
                for key in entry:
                    data[key] = entry[key]
                if not self._process(process_entry):
                    return False
            return True
        else:
            return self._process(process_entry)

    def _process(self, process_entry):

        data = {}
        if self.upload_params is not None:
            for i in self.upload_params:
                data[i] = self.upload_params[i]

        for i in process_entry.data.config_delegate:
            data[i] = process_entry.data.config_delegate[i]

        try:
            url = self.url
            if self.format_url:
                self.logger.debug(process_entry[constants.data][constants.url_parameters])
                url = self.url.format(**process_entry[constants.data][constants.url_parameters])
                self.logger.debug(url)
            r = requests.post(url, data=data['payload'], headers=self.headers, auth=self.auth, **self.request_kw)

            # self.logger.info("HTTP Response: %s %s" % (r.status_code, r.reason))
            self.logger.info("HTTP Response: %s" % (r.status_code))

            response = r.raw.read()
            self.logger.log(5, response)
            # r.connection.close()
            if r.status_code in self.success_http_codes:
                return True
            elif r.status_code in self.reject_http_codes:
                raise HTTPError(r.status_code, response)
            else:
                self.logger.error("Upload Error, sleeping for %s seconds" % self.upload_error_sleep)
                time.sleep(self.upload_error_sleep)
                return False

        except HTTPError, he:
            raise BadDataException(he)

        except Exception, e:
            self.logger.exception(e)
            self.logger.error("Unknown error: %s" % e.message)
            time.sleep(self.upload_error_sleep)
            return False


class HTTPError(StandardError):
    def __init__(self, code, message, *args, **kwargs):
        StandardError.__init__(self, message, *args, **kwargs)
        self.code = code
        self.message = message
