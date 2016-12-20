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

from serial_grabber.archive import *
from serial_grabber.cache import FileSystemCache, FactoryNamespacedCache
from serial_grabber.util import RollingFilename, PreviousWeekStartBoundary, week_period, to_date_format


storage_archive = JSONLineArchive(
    SerialGrabber_Paths.archive_dir,
    RollingFilename(
        PreviousWeekStartBoundary(),
        week_period,
        None,
        to_date_format
    )
)

storage_cache = FileSystemCache(SerialGrabber_Paths.cache_dir, storage_archive)

cache_factory = lambda basename, namespace, archive: FileSystemCache(os.path.join(basename, namespace, "messages"), archive)
archive_factory = lambda basename, namespace: JSONLineArchive(os.path.join(basename, namespace, "message_archive"), RollingFilename(
    PreviousWeekStartBoundary(),
    week_period,
    None,
    to_date_format
))

message_cache = FactoryNamespacedCache(SerialGrabber_Paths.message_cache_dir, cache_factory, archive_factory)