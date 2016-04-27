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
import base64
import pickle
from serial_grabber import constants

from serial_grabber.reader import Reader
from serial_grabber.extractors import LineTransactionExtractor
import time
import json


class FileReader(Reader):
    """
    A reader that opens and reads a file for its input.

    :param transaction_extractor: The transaction extractor used to parse the input stream.
    :type transaction_extractor: :py:class:`serial.grabber.reader.TransactionExtractor`
    :param str filename: The file to open and read as input.
    """
    def __init__(self, transaction_extractor, filename):
        Reader.__init__(self, transaction_extractor, 0)
        self.filename = filename

    def setup(self):
        self.stream = open(self.filename, "rb")

    def close(self):
        if 'stream' in self.__dict__ and self.stream:
            self.stream.close()
            self.stream = None

    def read_data(self):
        return self.stream.read(1)

class JSONLineFileReader(Reader):
    """

    """
    def __init__(self, filename, inter_record_delay=0):
        Reader.__init__(self, LineTransactionExtractor(), 0)
        self.filename = filename
        self.inter_record_delay = inter_record_delay

    def setup(self):
        self.stream = open(self.filename, "rb")

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None

    def read_data(self):
        return self.stream.read(1)

    def handle_transaction(self, stream_id, emit):
        entry = json.loads(emit)
        if constants.binary in entry and entry[constants.binary]:
            # entry[constants.payload] = pickle.loads(base64.b64decode(entry[constants.payload]))
            entry[constants.payload] = base64.b64decode(entry[constants.payload])
        self.storage_cache.cache(entry)
        self.logger.info("End of Transaction")
        self.counter.read()
        self.counter.update()
        time.sleep(self.inter_record_delay)

