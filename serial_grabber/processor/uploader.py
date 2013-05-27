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

import os, cache, requests, logging, time, datetime
import SerialGrabber_Paths, SerialGrabber_Settings
import httplib, urllib, socket
from urlparse import urlparse

from StringIO import StringIO

class Uploader:
    logger = logging.getLogger("Uploader")

    def __call__(self, *args, **kwargs):
        try:
            self.logger.info("Uploader Thread Started.")
            self.isRunning, self.counter = args
            socket.setdefaulttimeout(15)
            self.run_uploader()
        except BaseException, e:
            self.logger.exception(e)

    def run_uploader(self):
        while self.isRunning.running:
            for entry in os.listdir(SerialGrabber_Paths.cache_dir):
                entry_path = os.path.join(SerialGrabber_Paths.cache_dir, entry)
                if os.path.isfile(entry_path):
                    try:
                        if self.post(entry_path, entry):
                            self.counter.processed()
                    except BaseException, e:
                        self.logger.error("Failed to upload data: %s"%e)
#                        self.logger.error(traceback.format_exception(*sys.exc_info())[0])
                        self.logger.exception(e)
            self.logger.log(5, "Uploader Sleeping.")
            time.sleep(SerialGrabber_Settings.uploader_sleep)

    def post(self, entry_path, entry):
        parts = entry.split("-")
        cache_time = float(parts[0].split(".")[0])
        current_time = time.mktime(datetime.datetime.now().timetuple())
        toRet = False
        #if the system clock get sets backwards we don't want the data to sit there for ever.
        if abs(cache_time - current_time) > SerialGrabber_Paths.uploader_collision_avoidance_delay:
#            self.post_requests(entry_path)
            self.post_httplib(entry_path)
            toRet = True
        else:
            self.logger.debug("File is to new. Leaving for next round.")
        return toRet

    def post_httplib(self, entry_path):
        url, payload = cache.read_cache(entry_path)
        params = urllib.urlencode(payload)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

        _url = urlparse(SerialGrabber_Paths.urls[url])
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
            cache.decache(entry_path)

    def post_requests(self, entry_path):
        url, payload = cache.read_cache(entry_path)
        s = requests.session()
        s.config['keep_alive'] = False
        s.config['danger_mode'] = True
        s.config['max_retries'] = 0
        s.config['pool_connections'] = 1
        s.config['pool_maxsize'] = 1

        r = s.post(SerialGrabber_Paths.urls[url], data=payload, verify=False)
        self.logger.info("Response Code: %s" % r.status_code)
        self.logger.debug(r.text.encode('utf8'))
        if r.status_code == requests.codes.ok:
            print "POSTED"
            cache.decache(entry_path)
            toRet = True
        r.raw.release_conn()
        del r
        del s
