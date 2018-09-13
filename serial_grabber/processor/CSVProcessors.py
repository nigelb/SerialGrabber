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
from csv import DictWriter, DictReader
import logging
from serial_grabber.processor import ExternalFilenameProcessor
import os.path

from serial_grabber.transform import IdentityTransform, Transform


class CSVTransform(Transform):
    """
    Return the row that is to be given to a CSVFileProcessor instead of a modified process_entry
    """
    def transform(self, process_entry):
        raise Exception('Method "transform" not implemented.')

class CSVFileProcessor(ExternalFilenameProcessor):
    """
    Converts the payload to a CSV file and appends it to *filename*

    :param string filename: The output location
    :param int permission: The file mode to set on the output file

    """
    logger = logging.getLogger("CSVFileProcessor")

    def __init__(self, filename=None, permission=0644, headers=None, transform=IdentityTransform()):
        self.field_names = headers
        if filename:
            self.setOutputFileName(filename)
        self.permission = permission
        self.transform = transform

    def setOutputFileName(self, filename):
        ExternalFilenameProcessor.setOutputFileName(self, filename)
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as csv_file:
                existing = DictReader(csv_file)
                self.field_names = existing.fieldnames


    def process(self, process_entry):
        data = self.transform.transform(process_entry)
        if not self.field_names:
            self.field_names = data.keys()
            self.field_names.sort()
        header = True
        if os.path.exists(self.filename):
            header = False
        with open(self.filename, "a") as csv_file:
            existing = DictWriter(csv_file, self.field_names)
            if header:
                existing.writeheader()
            existing.writerow(data)
        if header:
            os.chmod(self.filename, self.permission)
        return True

    def run(self):
        raise Exception("No!")




