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
from serial_grabber.processor import Processor


class FileAppenderProcessor(Processor):
    """
    Append the contents of the transactions payload to *output_file*.

    :param string output_file: The name of the file to append to.
    """

    def __init__(self, output_file):
        self.output_file = output_file

    def process(self, process_entry):
        try:
            with open(self.output_file, "a+b") as out_f:
                # print cache_entry.data
                out_f.write(process_entry.data.payload)
                out_f.write("\n")
            return True
        except:
            import traceback

            traceback.print_exc()
            return False
