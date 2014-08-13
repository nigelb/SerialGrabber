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

import glob
import pickle
import shutil
import os
import os.path
import logging
import json
import base64

import constants
from serial_grabber.util import config_helper, get_millis


def cache_cmp(a, b):
    _a_t, a_ext = a.split('.')
    _b_t, b_ext = b.split('.')
    a_1, a_2 = _a_t.split("-")
    b_1, b_2 = _b_t.split("-")
    v = int(a_1) - int(b_1)
    if v != 0: return int(v)
    return int(int(a_2) - int(b_2))


def make_payload(data, binary=False):
    return {
        constants.payload: data,
        constants.timep: get_millis(),
        constants.binary: binary
    }


class Cache:
    logger = logging.getLogger("Cache")

    def __init__(self, cache_dir, archive):
        self.cache_dir = cache_dir
        self.archive = archive


    def list_cache(self):
        raise Exception("Not Implemented")

    def read_cache(self, cache_filename):
        raise Exception("Not Implemented")

    def make_payload(self, data, binary=False):
        raise Exception("Not Implemented")

    def cache(self, payload):
        raise Exception("Not Implemented")

    def decache(self, cache_file, type="archive"):
        raise Exception("Not Implemented")

    def close_cache(self):
        raise Exception("Not Implemented")


class FileSystemCache(Cache):
    def list_cache(self):
        toRet = {}
        for _entry in glob.glob(os.path.join(self.cache_dir, "*.data")):
            entry_path = _entry
            entry = os.path.basename(_entry)
            toRet[entry] = entry_path
        order = toRet.keys()
        order.sort(cache_cmp)
        return order, toRet

    def read_cache(self, cache_filename):
        with open(cache_filename, "rb") as cache_file:
            try:
                cache_entry = json.load(cache_file)
                if constants.binary in cache_entry and cache_entry[constants.binary]:
                    cache_entry[constants.payload] = pickle.loads(base64.b64decode(cache_entry[constants.payload]))
                if not (cache_entry.has_key(constants.timep)) and not (cache_entry.has_key(constants.payload)):
                    self.logger.error("Corrupted Cache Entry: %s de-caching." % cache_filename)
                    self.decache(cache_filename)
                    return None
                return config_helper(cache_entry)
            except ValueError, ve:
                self.logger.error("Corrupted Cache Entry: %s de-caching." % cache_filename)
                self.decache(cache_filename)
                return None

    def cache(self, payload):
        if constants.binary in payload and payload[constants.binary]:
            payload[constants.payload] = base64.b64encode(pickle.dumps(payload[constants.payload]))
        cache_file_path = os.path.join(self.cache_dir, "%s-0.data" % payload[constants.timep])
        tmp_file_path = os.path.join(self.cache_dir, "%s-0.tmp" % payload[constants.timep])
        n = 1
        while os.path.exists(cache_file_path):
            cache_file_path = os.path.join(self.cache_dir, "%s-%s.data" % (payload[constants.timep], n))
            tmp_file_path = os.path.join(self.cache_dir, "%s-%s.tmp" % (payload[constants.timep], n))
            n += 1

        with open(tmp_file_path, "wb") as cache_file:
            json.dump(payload, cache_file)
        shutil.move(tmp_file_path, cache_file_path)
        self.logger.debug("Wrote cache file: %s" % cache_file_path)

    def decache(self, cache_file, type="archive"):
        if self.archive.archive(cache_file, type):
            self.logger.info("decached %s" % os.path.basename(cache_file))
            if os.path.exists(cache_file):
                self.logger.error("Archiver did not remove file, deleting: %s" % os.path.basename(cache_file))
                os.remove(cache_file)


    def close_cache(self):
        self.archive.close()