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
import glob

import shutil, os, os.path, constants, time, logging, json
from datetime import datetime
from serial_grabber.util import config_helper, get_millis
import tarfile

import SerialGrabber_Paths

logger = logging.getLogger("Cache")

archive = {}

def open_archive(depth=0, name="archive"):
    if depth == 2:
        return None
    global archive
    if name in archive:
        return archive[name]
    if not os.path.exists(SerialGrabber_Paths.archive_dir):
        os.makedirs(SerialGrabber_Paths.archive_dir)
    archive_path = os.path.join(SerialGrabber_Paths.archive_dir, "%s.tar"%name)
    archive_existed = os.path.exists(archive_path)
    try:
        archive[name] = tarfile.open(archive_path,"a")
    except:
        if archive_existed:
            n = datetime.now()
            while os.path.exists(os.path.join(SerialGrabber_Paths.archive_dir, "%s-%s.tar"%(name, n.strftime("%Y_%m_%d_%H_%M_%S")))):
                n = datetime.now()
            old_archive_path = os.path.join(SerialGrabber_Paths.archive_dir, ("%s-%s.tar"%(name, n.strftime("%Y_%m_%d_%H_%M_%S"))))
            logger.error("Could not open archive.tar, moving to %s and starting new archive."%old_archive_path)
            shutil.move(archive_path, old_archive_path)
            return open_archive(depth=depth+1)
    return archive

def close_cache():
    global archive
    for name in archive:
        archive[name].close()
    logger.warn("Closed cache.")


def cache_cmp(a,b):
    _a_t, a_ext = a.split('.')
    _b_t, b_ext = b.split('.')
    a_1, a_2 = _a_t.split("-")
    b_1, b_2 = _b_t.split("-")
    v = int(a_1) - int(b_1)
    if v != 0: return int(v)
    return int(int(a_2) - int(b_2))

def list_cache():
    toRet = {}
    for _entry in glob.glob(os.path.join(SerialGrabber_Paths.cache_dir, "*.data")):
        entry_path = _entry
        entry = os.path.basename(_entry)
        toRet[entry] = entry_path
    order = toRet.keys()
    order.sort(cache_cmp)
    return order, toRet

def read_cache(cache_filename):
    with open(cache_filename, "rb") as cache_file:
        try:
            cache_entry = json.load(cache_file)
            if not (cache_entry.has_key(constants.timep)) and not (cache_entry.has_key(constants.payload)):
                logger.error("Corrupted Cache Entry: %s de-caching."%cache_filename)
                decache(cache_filename)
                return None
            return config_helper(cache_entry)
        except ValueError, ve:
            logger.error("Corrupted Cache Entry: %s de-caching."%cache_filename)
            decache(cache_filename)
            return None

def make_payload(data):
    toRet =  {
        constants.payload: data,
        constants.timep: get_millis()
    }
    return toRet

def cache(payload):
    cache_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s-0.data"%payload[constants.timep])
    tmp_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s-0.tmp"%payload[constants.timep])
    n = 1
    while os.path.exists(cache_file_path):
        cache_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s-%s.data"%(payload[constants.timep], n))
        tmp_file_path = os.path.join(SerialGrabber_Paths.cache_dir, "%s-%s.tmp"%(payload[constants.timep], n))
        n += 1

    with open(tmp_file_path, "wb") as cache_file:
        json.dump(payload, cache_file)
    shutil.move(tmp_file_path, cache_file_path)
    logger.debug("Wrote cache file: %s"%cache_file_path)

def decache(cache_file, type="archive"):
    if os.path.exists(cache_file):
        shutil.move(cache_file, SerialGrabber_Paths.archive_dir)
        _archive = open_archive(name=type)
        name = os.path.basename(cache_file)
        archived_name = os.path.join(SerialGrabber_Paths.archive_dir, name)
        _archive.add(archived_name, arcname=os.path.join("archive",name))
        os.remove(archived_name)
        logger.info("decached %s"%os.path.basename(archived_name))

