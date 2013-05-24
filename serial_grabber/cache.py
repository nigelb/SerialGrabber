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

import shutil, os, os.path, constants, datetime, time, logging, json
import SerialGrabber_Paths
from serial_grabber.util import config_helper
import tarfile

logger = logging.getLogger("Cache")

def open_archive():
    if not os.path.exists(SerialGrabber_Paths.archive_dir):
        os.makedirs(SerialGrabber_Paths.archive_dir)
    archive_path = os.path.join(SerialGrabber_Paths.archive_dir, "archive.tar")
    return tarfile.open(archive_path,"a")

def cache_cmp(a,b):
    a_t, a_s, a_ext = a.split('.')
    b_t, b_s, b_ext = b.split('.')
    a_t = int(b_t)
    b_t = int(b_t)
    v = a_t - b_t
    if v != 0: return v
    a_s = int(a_s.replace("0-",""))
    b_s = int(b_s.replace("0-",""))
    return a_s - b_s

def list_cache():
    toRet = {}
    for entry in os.listdir(SerialGrabber_Paths.cache_dir):
        entry_path = os.path.join(SerialGrabber_Paths.cache_dir, entry)
        toRet[entry] = entry_path
    order = toRet.keys()
    order.sort(cache_cmp)
    return order, toRet

def read_cache(cache_filename):
    with open(cache_filename, "rb") as cache_file:
        cache_entry = json.load(cache_file)
        if not (cache_entry.has_key(constants.timep)) and not (cache_entry.has_key(constants.payload)):
            logger.error("Corrupted Cache Entry: %s de-caching."%cache_filename)
            decache(cache_filename)
            return None
        return config_helper(cache_entry)

def make_payload(data):
    toRet =  {
        constants.payload: data,
        constants.timep: time.mktime(datetime.datetime.now().timetuple())
    }
    return toRet

def cache(payload):
    cache_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s.data"%payload[constants.timep])
    n = 1
    while os.path.exists(cache_file_path):
        cache_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s-%s.data"%(payload[constants.timep], n))
        n += 1
    cache_file = open(cache_file_path, "wb")
    json.dump(payload, cache_file)
    logger.debug("Wrote cache file: %s"%cache_file_path)

def decache(cache_file):
    if os.path.exists(cache_file):
        shutil.move(cache_file, SerialGrabber_Paths.archive_dir)
        with open_archive() as archive:
            name = os.path.basename(cache_file)
            archived_name = os.path.join(SerialGrabber_Paths.archive_dir, name)
            archive.add(archived_name, arcname=os.path.join("archive",name))
            os.remove(archived_name)

