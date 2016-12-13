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

import os

#Directories
data_logger_dir = None
if "APPDATA" in os.environ:
    data_logger_dir = os.path.join(os.environ["APPDATA"], "datalogger")
else:
    data_logger_dir = os.path.join(os.path.expanduser("~"), ".datalogger")

cache_dir = os.path.join(data_logger_dir, "cache")
archive_dir = os.path.join(data_logger_dir, "archive")
node_map_dir = os.path.join(data_logger_dir, "nodes")

