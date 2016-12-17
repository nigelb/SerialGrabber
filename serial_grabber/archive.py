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

import SerialGrabber_Paths
import logging
import os, tarfile
import shutil
from serial_grabber.util import get_millis


class BaseArchive:
    logger = logging.getLogger("Archive")

    def __init__(self, archive_dir):
        self.archive_dir = archive_dir
        self.archives = {}

    def open(self, depth=0, name="archive"):
        raise Exception("Not Implemented")

    def archive(self, to_archive, name="archive"):
        raise Exception("Not Implemented")

    def close(self):
        raise Exception("Not Implemented")


# class TarArchive(BaseArchive):
# def __init__(self, archive_dir):
#         BaseArchive.__init__(self, archive_dir)
#
#     def open(self, depth=0, name="archive"):
#         """
#         The archived transactions are stored in a tar file
#         """
#         if depth == 2:
#             return None
#         global archive
#         if name in archive:
#             return archive[name]
#         if not os.path.exists(SerialGrabber_Paths.archive_dir):
#             os.makedirs(SerialGrabber_Paths.archive_dir)
#         archive_path = os.path.join(SerialGrabber_Paths.archive_dir, "%s.tar" % name)
#         archive_existed = os.path.exists(archive_path)
#         try:
#             archive[name] = tarfile.open(archive_path, "a")
#         except:
#             if archive_existed:
#                 n = datetime.now()
#                 while os.path.exists(os.path.join(SerialGrabber_Paths.archive_dir,
#                                                   "%s-%s.tar" % (name, n.strftime("%Y_%m_%d_%H_%M_%S")))):
#                     n = datetime.now()
#                 old_archive_path = os.path.join(SerialGrabber_Paths.archive_dir,
#                                                 ("%s-%s.tar" % (name, n.strftime("%Y_%m_%d_%H_%M_%S"))))
#                 self.logger.error(
#                     "Could not open archive.tar, moving to %s and starting new archive." % old_archive_path)
#                 shutil.move(archive_path, old_archive_path)
#                 return self.tar_open_archive(depth=depth + 1)
#         return archive[name]
#
#     def close(self):
#         for name in self.archives:
#             archive[name].close()
#         self.logger.warn("Closed cache.")


class FileSystemArchive(BaseArchive):
    """
    A :py:class:`serial_grabber.archive.BaseArchive` implementation that moves the cache entry from the cache directory
    to the archive directory.

    :param str archive_dir: The directory in which to store the archive files.
    """
    def __init__(self, archive_dir):
        BaseArchive.__init__(self, archive_dir)
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

    def archive(self, to_archive, name="archive"):
        try:
            shutil.move(to_archive, SerialGrabber_Paths.archive_dir)
            return True
        except Exception, e:
            self.logger.error("Error archiving file: %s: %s" % (to_archive, e.message))
        return False

    def close(self):
        pass


class DumpArchive(BaseArchive):
    """
    A :py:class:`serial_grabber.archive.BaseArchive` implementation that deletes the cache entry data from the cache.
    """
    def close(self):
        pass

    def archive(self, to_archive, name="archive"):
        os.remove(to_archive)

    def open(self, depth=0, name="archive"):
        pass


class JSONLineArchive(BaseArchive):
    """
    A :py:class:`serial_grabber.archive.BaseArchive` implementation that stores each cache entry as a JSON encoded line
    within the archive file.

    :param str archive_dir: The directory in which to store the archive files.
    :param filename_roller: The filename roller to use.
    :type filename_roller: :py:class:`serial_grabber.util.RollingFilename` or None
    """
    def __init__(self, archive_dir, filename_roller=None):
        BaseArchive.__init__(self, archive_dir)
        self.filename_roller = filename_roller

    def close(self):
        for _archive in self.archives:
            try:
                self.archives[_archive].close()
            except Exception, e:
                self.logger.error("Error closing archive: %s: %s" % (_archive, e.message))
        self.archives = {}

    def archive(self, to_archive, name="archive"):
        try:
            if not os.path.exists(self.archive_dir):
                os.makedirs(self.archive_dir)
            with open(os.path.join(self.archive_dir, self.get_name(name)), "ab") as _output:
                with open(to_archive, "rb") as _input:
                    _output.write(_input.read())
                    _output.write("\n")
            os.remove(to_archive)
            return True
        except Exception, e:
            self.logger.error("Error archiving file: %s: %s" % (to_archive, e.message))
        return False

    def get_name(self, name="archive"):
        if self.filename_roller is not None:
            return self.filename_roller.calculate_output_name("%s_{ts}.json"%name, get_millis())
        return "%s.json" % name
