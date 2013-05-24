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
import csv
from serial_grabber.util import config_helper

class CsvCalibrationData:
    def __init__(self, calibration_file, id_field):
        self.data = {}
        with open(calibration_file, "rb") as data:
            a = csv.DictReader(data)
            for i in a:
                self.data[i[id_field]] = i

    def __getitem__(self, key):
        return config_helper(self.__dict__["data"][key])


    def __contains__(self, key):
        return key in self.__dict__["data"]

if __name__ == "__main__":
    a = CsvCalibrationData("example/calibration.csv", "ID")
#    print a['2828F407030000D2'].M
    print '2828F407030000D2a' in a
