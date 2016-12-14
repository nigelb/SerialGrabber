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

from serial_grabber.reader.Xbee import MessageVerifier


class XBeeMessageVerifier(MessageVerifier):
    logger = logging.getLogger("MessageVerifier")
    def verify_message(self, transaction):
        self.logger.info(transaction)
        try:
            data = transaction.split("\n")
            if int(data[-2]) == len("\n".join(data[1:-2])):
                return True, "OK"
            else:
                self.logger.error("Reported length: %s, Actual length: %s"%(int(data[-2]), len("\n".join(data[1:-2]))))
                raise ValueError()
        except ValueError, e:
            self.logger.error("Could not convert %s to an integer."%data[-2])
            return False, "NA"

