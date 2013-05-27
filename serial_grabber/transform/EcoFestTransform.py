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
from datetime import datetime, timedelta
import logging
import time
from pprint import pprint
from serial_grabber.transform import Transform
from serial_grabber.util import config_helper
import SerialGrabber_Calibration

EPOCH = datetime(2000, 1 , 1, 0, 0, 0, 0)

def calculate_humidity(temp, Vs, Vo):

    d = 0.1515
    c = 0.00636

    e = 1.0546
    f = 0.00216

    sensor_rh = ((Vo / Vs) - d) / c
    true_rh = sensor_rh / (e - (f * temp))
    return true_rh

class EcoFestTransform(Transform):
    logger = logging.getLogger("EcoFestTransform")
    def __init__(self):
        self.temp_calibration = None
        if "ECOFEST_TEMPERATURE_CALIBRATION" in SerialGrabber_Calibration.__dict__:
            self.temp_calibration = SerialGrabber_Calibration.ECOFEST_TEMPERATURE_CALIBRATION
        self.humidity_calibration = None
        if "ECOFEST_HUMIDITY_CALIBRATION" in SerialGrabber_Calibration.__dict__:
            self.humidity_calibration = SerialGrabber_Calibration.ECOFEST_HUMIDITY_CALIBRATION

    def transform(self, process_entry):
        transform_result = config_helper({})
        for i in process_entry:
            transform_result[i] = process_entry[i]
        transform_result.data = config_helper({})
        for i in process_entry.data:
            transform_result.data[i] = process_entry.data[i]

        original_payload = transform_result.data.payload
        _temp, _hum = process_entry.data.payload.split("END TEMPERATURE")
        temp = _temp.strip().split("BEGIN TEMPERATURE")[1].strip().split("\n")
        hum = _hum.split("BEGIN HUMIDITY")[1].split("END HUMIDITY")[0].strip().split("\n")
        first = None

        result = {}
        for temp_entry in temp:
            temp_line = temp_entry.split(",")
            if len(temp_line) == 3:
                _time, address, temp = temp_line
                _time = EPOCH + timedelta(seconds=int(_time))
                if first is None:
                    first = time.mktime(_time.timetuple())
                    result[first] = {}
                    result[first]["temperature"] = {}
                temp = float(temp)
                if self.temp_calibration:
                    temp = self.temp_calibration.calibrate(address, temp)
                result[first]["temperature"][str(address)] = temp
            else:
                self.logger.error("Invalid Temperature line: %s"%temp_entry)

        result[first]["humidity"] = {}
        for hum_entry in hum:
            humidity_line = hum_entry.split(",")
            if len(humidity_line) == 5:
                _time, address, temp, v1, v2 = humidity_line
                rh = calculate_humidity(float(temp), float(v1), float(v2))
                if self.humidity_calibration:
                    rh = self.humidity_calibration.calibrate(address, rh)
                result[first]["humidity"][str(address)] = rh
            else:
                self.logger.error("Invalid line: %s"%hum_entry)

        transform_result.data.payload = result
        transform_result.data.original_payload = original_payload
        return transform_result

