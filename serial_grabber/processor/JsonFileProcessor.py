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
import json

import logging
import shutil
import tempfile
from serial_grabber.processor import Processor

import os, os.path


class JsonFileProcessor(Processor):
    logger = logging.getLogger("JsonFileProcessor")

    def __init__(self, output_file, transaction_filter=None, limit=-1, permission=0644):
        self.filter = transaction_filter
        self.limit = limit
        self.output_file = output_file
        self.permission = permission
        _dir = os.path.dirname(os.path.abspath(output_file))
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        self.data = []
        if os.path.exists(self.output_file):
            with open(self.output_file, "rb") as existing:
                data = json.load(existing)
            for i in data:
                self.data.append(json.dumps(i))


    def process(self, process_entry):
        filtered = False
        if self.filter:
            filtered = self.filter.filter(process_entry)
        self.logger.debug("Filtered: %s, %s" % (filtered, self.output_file))
        try:
            if not filtered:
                if self.limit > 0 and len(self.data) >= self.limit:
                    self.data = self.data[((self.limit - 1 ) * -1):]
                    if (self.limit - 1) == 0:
                        self.data = []
                self.data.append(json.dumps(process_entry.data.payload.config_delegate))
                fid, path = tempfile.mkstemp()
                with os.fdopen(fid, "wb") as out_data:
                    out_data.write("[")
                    out_data.write(",".join(self.data))
                    out_data.write("]")
                os.chmod(path, self.permission)
                shutil.move(path, self.output_file)
                return True
        except:
            import traceback

            traceback.print_exc()
            return False






