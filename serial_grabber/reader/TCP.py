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


from serial_grabber.reader import Reader
import socket

class TCPReader(Reader):

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def getCommandStream(self):
        return self

    def close(self):
        self.soc.close()
        del self.soc

    def setup(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.hostname, self.port))
        self.soc = s
        self.stream = self

    def readline(self):
        data = []
        while True:
            dat = self.soc.recv(1)
            if dat:
                if dat == "\n":
                    return "".join(data)
                data.append(dat)

    def write(self, data):
        self.soc.sendall(data)