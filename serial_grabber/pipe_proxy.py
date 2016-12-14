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
from StringIO import StringIO

import logging

import os

STATUS="STATUS"
VALUE="VALUE"
EXCEPTION="EXCEPTION"
PID="PID"
STATUS_OK="OK"
STATUS_EXCEPTION="EXC"

def expose_object(endpoint, object):
    from threading import Thread
    logger = logging.getLogger(str(object))

    def handler(endpoint, object):
            running = True
            while running:
                try:
                    call = endpoint.recv()
                    if call[0] == "__close__":
                        running = False
                        endpoint.send({STATUS: STATUS_OK, VALUE:None})
                        return
                    param = getattr(object, call[0])
                    if hasattr(param, "__call__"):
                        param = param.__call__( *call[1], **call[2])
                    endpoint.send({STATUS: STATUS_OK, VALUE:param})
                except Exception as e:
                    import traceback
                    file=StringIO()
                    traceback.print_exc(file=file)
                    endpoint.send({STATUS: STATUS_EXCEPTION, EXCEPTION: e, VALUE: file.getvalue(), PID: os.getpid()})
                    file.close()

    handler = Thread(target=handler, args=(endpoint, object))
    handler.setDaemon(True)
    handler.start()

class RemoteException(Exception):
    def __init__(self, exception, traceback, pid):
        self.exception = exception
        self.traceback = traceback
        self.pid = pid

    def __str__(self):
        return "%s in prosess: %s: %s:\r\n%s"%(type(self.exception).__name__, self.pid, self.exception.__str__(), self.traceback)


class ProxyCall:
    def __init__(self, endpoint, name):
        self.name = name
        self.endpoint = endpoint

    def __call__(self, *args, **kwargs):
        self.endpoint.send((self.name, args, kwargs))
        result = self.endpoint.recv()
        if result[STATUS] == STATUS_OK:
            return result[VALUE]
        if result[STATUS] == STATUS_EXCEPTION:
            raise RemoteException(result[EXCEPTION], result[VALUE], result[PID])


class PipeProxy:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __getattr__(self, item):
        return ProxyCall(self.endpoint, item)

    def __getattribute__(self, item):
        return ProxyCall(self.endpoint, item)