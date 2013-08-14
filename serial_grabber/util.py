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
        if key is "__str__": return self.config.__str__
        elif key is "__repr__": return self.config.__repr__
        elif key is "__iter__": return self.config.__iter__
        elif key is "config_delegate": return self.config
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

def get_millis(dt = None):
    if dt is None:
        dt = datetime.datetime.now()
    return  int((time.mktime(dt.timetuple()) * 1000) + (dt.microsecond / 1000))

def PreviousWeekStartBoundry():
    _dt = datetime.datetime.now()
    return get_millis(dt = _dt.replace(day=(_dt.day - (_dt.weekday() + 1 )), hour=0, minute=0, second=0, microsecond=0))

def PreviousMidnightBoundry():
    dt = datetime.datetime.now()
    return get_millis(dt = dt.replace(hour=0, minute=0, second=0, microsecond=0))