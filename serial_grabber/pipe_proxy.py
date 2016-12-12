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


def expose_object(endpoint, object):
    from threading import Thread
    def handler(endpoint, object):
            while True:
                try:
                    call = endpoint.recv()
                    param = getattr(object, call[0])
                    if hasattr(param, "__call__"):
                        param = param.__call__( *call[1], **call[2])
                    endpoint.send(param)
                except Exception as e:
                    import traceback
                    traceback.print_exc()

    handler = Thread(target=handler, args=(endpoint, object))
    handler.setDaemon(True)
    handler.start()

class ProxyCall:
    def __init__(self, endpoint, name):
        self.name = name
        self.endpoint = endpoint

    def __call__(self, *args, **kwargs):
        self.endpoint.send((self.name, args, kwargs))
        return self.endpoint.recv()

class PipeProxy:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __getattr__(self, item):
        return ProxyCall(self.endpoint, item)

    def __getattribute__(self, item):
        return ProxyCall(self.endpoint, item)