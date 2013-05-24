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

import logging
from serial_grabber.calibration import Calibration


class LinearCalibration(Calibration):
    logger = logging.getLogger("LinearCalibration")
    def __init__(self, calibration_data):
        self.calibration_data = calibration_data

    def calibrate(self, id, value):
        if id in self.calibration_data:
            cd = self.calibration_data[id]
            return (value * float(cd.M)) + float(cd.B)
        self.logger.warn("Cannot find calibration for ID: %s"%id)
        return value
