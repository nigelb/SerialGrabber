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


class TransactionExtractor:
    """
    A TransactionExtractor reads a stream and breaks it into transactions (also knows a payloads) beginning at the
    *start_boundary* and ending at the *stop_boundary*. Once it has created a transaction it passes the payload to the
    specified *callback*. Most :py:class:`serial.grabber.reader.Reader` implementations will set this callback.

    :param str stream_id: The id of the stream that this TransactionExtractor is attached to.
    :param str start_boundary: The string that specifies the beginning of the transaction.
    :param str stop_boundary: The string that specifies the end of the transaction.
    :param callback: The function called with the contents of the transaction
    :type callback: fn(stream_id, emit) or None
    """
    def __init__(self, stream_id, start_boundary, stop_boundary, callback=None):
        self.stream_id = stream_id
        self.start_boundary = start_boundary
        self.stop_boundary = stop_boundary
        self.buffer = ""
        self.callback = callback

    def set_callback(self, callback):
        self.callback = callback

    def write(self, data):
        self.buffer += data
        start = self.buffer.find(self.start_boundary)
        if start >= 0:
            self.buffer = self.buffer[start:]
        end = self.buffer.find(self.stop_boundary, len(self.start_boundary))
        if end > 0:
            emit = self.buffer[:end + len(self.stop_boundary)]
            self.buffer = self.buffer[end + len(self.stop_boundary):]
            self.callback(self.stream_id, emit)


class LineTransactionExtractor:
    """

    """
    def __init__(self, callback=None):
        self.buffer = ""
        self.callback = callback

    def set_callback(self, callback):
            self.callback = callback

    def write(self, data):
        self.buffer += data
        if data == '\n':
            self.callback(None, self.buffer)
            self.buffer = ""
