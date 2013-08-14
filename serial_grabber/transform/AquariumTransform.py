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
from serial_grabber.transform import Transform
from serial_grabber.util import config_helper

def __temp(args):
    name, temp, tempSetPoint = args
    return "Temperature", {"Temperature_temp": temp, "Temperature_set_point": tempSetPoint}


def __ph(args):
    name, ph, phSetPoint = args
    return "PH", {"PH_ph": ph, "PH_set_point": phSetPoint}


def __tempPID(args):
    name, kp, ki, kd, pidVal = args
    return "TemperaturePID", {"TemperaturePID_Kp": kp, "TemperaturePID_Ki": ki, "TemperaturePID_Kd": kd, "TemperaturePID_pid_val": pidVal}


def __phPID(args):
    name, kp, ki, kd, pidVal = args
    return "PHPID", {"PHPID_Kp": kp, "PHPID_Ki": ki, "PHPID_Kd": kd, "PHPID_pid_val": pidVal}

row_map = {
    "temp": __temp,
    "ph": __ph,
    "temp_pid": __tempPID,
    "ph_pid": __phPID,
}

class AquariumTransform(Transform):
    def transform(self, process_entry):
        transform_result = config_helper({})
        for i in process_entry:
            transform_result[i] = process_entry[i]
        transform_result.data = config_helper({})
        for i in process_entry.data:
            transform_result.data[i] = process_entry.data[i]

        original_payload = transform_result.data.payload
        result = {}
        lines = original_payload.split('\n')[1:-1]
        for i in lines:
            val = i.split(",")
            if val[0] in row_map.keys():
                id, dat = row_map[val[0]](val)
                for j in dat.keys():
                    result[j] = dat[j]
#                result[id] = dat
        result['ts'] = process_entry.data.time
        transform_result.data.payload = result
        transform_result.data.original_payload = original_payload
        return transform_result


def averageAquariumData(data):
    result = config_helper({
#        'PHPID': {"Kp": 0, "Ki": 0, "Kd": 0, "pid_val": 0},
#        "TemperaturePID": {"Kp": 0, "Ki": 0, "Kd": 0, "pid_val": 0},
#        "PH": {"ph": 0, "set_point": 0},
#        "Temperature": {"temp": 0, "set_point": 0}
        "PHPID_Kp": 0, "PHPID_Ki": 0, "PHPID_Kd": 0, "PHPID_pid_val": 0,
        "TemperaturePID_Kp": 0, "TemperaturePID_Ki": 0, "TemperaturePID_Kd": 0, "TemperaturePID_pid_val": 0,
        "PH_ph": 0, "PH_set_point": 0,
        "Temperature_temp": 0, "Temperature_set_point": 0
    })
    _time = 0
    for element in data:
        _time += element.data.time
        result.PHPID_Kp += float(element.data.payload.PHPID_Kp)
        result.PHPID_Ki += float(element.data.payload.PHPID_Ki)
        result.PHPID_Kd += float(element.data.payload.PHPID_Kd)

        result.TemperaturePID_Kp += float(element.data.payload.TemperaturePID_Kp)
        result.TemperaturePID_Ki += float(element.data.payload.TemperaturePID_Ki)
        result.TemperaturePID_Kd += float(element.data.payload.TemperaturePID_Kd)


        result.PH_ph += float(element.data.payload.PH_ph)
        result.PH_set_point += float(element.data.payload.PH_set_point)

        result.Temperature_temp += float(element.data.payload.Temperature_temp)
        result.Temperature_set_point += float(element.data.payload.Temperature_set_point)


    length = len(data)
    result.PHPID_Kp /= length
    result.PHPID_Ki /= length
    result.PHPID_Kd /= length

    result.TemperaturePID_Kp /= length
    result.TemperaturePID_Ki /= length
    result.TemperaturePID_Kd /= length

    result.PH_ph /= length
    result.PH_set_point /= length

    result.Temperature_temp /= length
    result.Temperature_set_point /= length
    result.timestamp = int(_time/length)
    toRet = {'data':{'payload':result.config_delegate, 'time':result.timestamp}}
    return config_helper(toRet)




