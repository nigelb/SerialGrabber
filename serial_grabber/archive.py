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

import SerialGrabber_Paths
from datetime import datetime
import logging
import os, tarfile
import shutil

logger = logging.getLogger("Archive")

archive = {}

def tar_open_archive(depth=0, name="archive"):
    """
    The archived transactions are stored in a tar file
    """
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
            return tar_open_archive(depth=depth+1)
    return archive[name]

def tar_close_cache():
    global archive
    for name in archive:
        archive[name].close()
    logger.warn("Closed cache.")

class FileArchive:

    def __init__(self, archive_name):
        self.archive_name = archive_name

    def add(self, name, arcname=None):
        with open(self.archive_name, "a") as out:
            with open(name, "rb") as _in:
                out.write(_in.read())
                out.write("\n")

    def close(self):pass

def file_open_archive(depth=0, name="archive"):
    global archive
    if name in archive:
        return archive[name]
    if not os.path.exists(SerialGrabber_Paths.archive_dir):
        os.makedirs(SerialGrabber_Paths.archive_dir)
    archive_path = os.path.join(SerialGrabber_Paths.archive_dir, "%s.archive"%name)
    archive[name] = FileArchive(archive_path)
    return archive[name]

def file_close_cache():
    global archive
    for name in archive:
        archive[name].close()
        del archive[name]
    logger.warn("Closed cache.")

class NoArchive:

    def add(self, name, arcname=None):pass
    def close(self):pass

def dump_open_archive(depth=0, name="archive"):
    return NoArchive()

def dump_close_cache(): pass