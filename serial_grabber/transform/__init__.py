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


class TransformException(Exception): pass
class DebugTransformException(Exception): pass

class Transform:
    def transform(self, process_entry):
        raise Exception('Method "transform" not implemented.')

class BlockAveragingTransform(Transform):
    import logging
    logger = logging.getLogger("AveragingTransform")
    def __init__(self, count, compute_average):
        self.count = count
        self.compute_average = compute_average
        self.values = []


    def transform(self, process_entry):
        self.values.append(process_entry)
        if len(self.values) == self.count:
            result = self.compute_average(self.values)
            self.values = []
            return result

        return None
