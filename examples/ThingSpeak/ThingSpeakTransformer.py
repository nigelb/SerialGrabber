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
from serial_grabber import constants
from serial_grabber.transform import Transform


api_key = "GT14ED5QGNLE2E8N"

field_map = {
    "1": "field8",
    "2": "field7",
    "3": "field6",
    "4": "field5",
    "5": "field4",
    "6": "field3",
    "7": "field2",
    "8": "field1",
}

# A Transform is used by a TransformProcessor to transform the data received
# from the reader into a form that can be used for the configured processor.
class ThingSpeakTransformer(Transform):

    def transform(self, process_entry):

        # Retrieve the transaction's data from the process_entry
        payload = process_entry[constants.data][constants.payload]

        transformed_data = {"api_key": api_key}

        # Process the retrieved data into
        lines = payload.split("\n")
        for line in lines:

            # Strip out the start and end delimiters
            if "SENSORS" in line:
                continue

            # Extract the sensor ID and value from the line
            sensor_id, sensor_value = line.split(",")
            sensor_value = sensor_value

            transformed_data[field_map[sensor_id]] = sensor_value

        process_entry[constants.data][constants.payload] = transformed_data
        return process_entry