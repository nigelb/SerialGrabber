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

from serial_grabber.state import matches, set_url, send_data, begin_transaction, end_transaction
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

def reader_state():
    READER_STATE = OrderedDict()
    READER_STATE[matches("BEGIN TEMPERATURE")] = begin_transaction(READER_STATE)
    READER_STATE[matches("END HUMIDITY")] = end_transaction(READER_STATE)
    return READER_STATE



