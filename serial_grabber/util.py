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
import datetime, time


class config_helper:
    def __init__(self, config):
        self.config = config

    def __setattr__(self, key, value):
        if key == "config":
            self.__dict__[key] = value
        else:
            self.config[key] = value

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, item):
        self.config[key] = item

    def __delitem__(self, key):
        del self.config[key]

    def __nonzero__(self):
        return True

    def __getattr__(self, key):
        if key is "__str__":
            return self.config.__str__
        elif key is "__repr__":
            return self.config.__repr__
        elif key is "__iter__":
            return self.config.__iter__
        elif key is "config_delegate":
            return self.config
        if type(self.config[key]) == dict:
            return config_helper(self.config[key])
        return self.config[key]

    def __contains__(self, item):
        try:
            self.__getattr__(item)
            return True
        except KeyError, e:
            return False


def locate_resource(name):
    import SerialGrabber_Paths, os.path

    search_path = [
        os.path.dirname(SerialGrabber_Paths.__file__),
        SerialGrabber_Paths.data_logger_dir
    ]

    for sp in search_path:
        path = os.path.join(sp, name)
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


def get_millis(dt=None):
    if dt is None:
        dt = datetime.datetime.now()
    return int((time.mktime(dt.timetuple()) * 1000) + (dt.microsecond / 1000))


week_period = 1000 * 60 * 60 * 24 * 7

def to_date_format(ts_millis):
    dt = datetime.datetime.fromtimestamp(ts_millis/1000)
    return dt.strftime("%Y_%m_%d-%H_%M_%S")


def PreviousWeekStartBoundary():
    _dt = datetime.datetime.now()
    _dt = _dt + datetime.timedelta(days=(-1 * (_dt.weekday() + 1 )))
    return get_millis(dt=_dt.replace(hour=0, minute=0, second=0, microsecond=0))


def PreviousMidnightBoundary():
    dt = datetime.datetime.now()
    return get_millis(dt=dt.replace(hour=0, minute=0, second=0, microsecond=0))


class RollingFilename:
    def __init__(self, boundary, period_ms, file_extension, ts_transform=lambda ts_millis: ts_millis):
        self.ts_transform = ts_transform
        self.boundary = boundary
        self.chunk_size = period_ms
        self.out_name = None
        self.file_extension = file_extension

    def calculate_output_name(self, pattern, ts):
        v = self.ts_transform((int((ts - self.boundary) / self.chunk_size) * self.chunk_size) + self.boundary)
        return pattern.format(ts=v, ext=self.file_extension)