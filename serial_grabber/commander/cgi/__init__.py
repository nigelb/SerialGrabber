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

from collections import defaultdict
import os, re, sys
from serial_grabber.util import config_helper

all_route = {}

def create_api_routes(name, api_name):
    global all_route
    def __init__(self, _route=None):
        if _route is not None:
            self.path = _route
            self.route_order.append(_route)
            self.__class__.route_order = sorted(self.route_order, lambda x,y: len(y) - len(x))

    def __call__(self, fn):
        self.routes[self.path] = fn
        return fn


    def route_request(self, uri):
        for r in self.route_order:
            m = re.match(r, uri)
            if m:
                return self.routes[r], m.groupdict()
        return None, None

    class_dict = {
        "__init__":__init__,
        "__call__":__call__,
        "route_request":route_request,
        "routes" : {},
        "route_order" : [],
        "api_name":api_name
    }
    toRet = type(name, (), class_dict)
    all_route[api_name] = toRet
    return toRet

def get_api_routes(api_name):
    global all_route
    return all_route[api_name]


class MetaDataAPIHandler:
    def __init__(self, config, api):
        self.config = config
        self.api = api
        self.headers = defaultdict(list)
        self.set_header("Content-Type", "text/html")

    def clear_header(self, key):
        if key in self.headers:
            del self.headers[key]

    def set_header(self, key, value):
        if key in ["Content-Type"]:
            self.clear_header(key)
        self.headers[key].append(value)

    def encode_results(self, request, results):
        raise Exception("Not Implemented")

    def handle(self):
        uri = os.environ['REQUEST_URI']
        if self.config.SERIAL_GRABBER_CGI_PREFIX:
            uri = uri.replace(self.config.SERIAL_GRABBER_CGI_PREFIX, "/", 1)
        Route = get_api_routes(self.api)
        routing = Route()
        method, request_values = routing.route_request(re.sub("/+", "/", uri))

        if method is None:
            self.set_header("Content-Type","text/plain")
            self.__render_output(501, "HTTP/1.1 501 Not Implemented")
            sys.exit(501)
        else:
            if self.config.SERIAL_GRABBER_ENABLE_CGITB:
                self.__handle_request(uri, method, request_values)
            else:
                try:
                    self.__handle_request(uri, method, request_values)
                except Exception, e:
                    print >> sys.stderr, "Error processing request:"
                    print >> sys.stderr, " %s"%e.message
                    self.set_header("Content-Type","text/plain")
                    self.__render_output(503, "HTTP/1.1 503 Service Unavailable")
                    sys.exit(503)

    def __handle_request(self, uri, method, request_values):
        remote_addr = os.environ['REMOTE_ADDR']
        request = config_helper({
            "request": sys.stdin.read(),
            "request_url": uri,
            "remote_addr": remote_addr,
            "set_header": lambda key, value: self.set_header(key, value)
        })
        for i in request_values:
            if i not in request:
                request[i] = request_values[i]
        results = method(request)
        self.__render_output(200, self.encode_results(request, results))

    def __render_output(self, status, content):
        print "Status:%s"%status
        for header in self.headers:
            for header_val in self.headers[header]:
                print "%s: %s"%(header, header_val)
        print ""
        print content

class metadata:
    metadata_funcs = {}

    def __init__(self, name=None, group="default"):
        self.name = name
        self.group = group

    def __call__(self, fn):
        if self.group not in self.metadata_funcs.keys():
            self.metadata_funcs[self.group] = []

        if self.name is None:
            self.metadata_funcs[self.group].append(fn.__name__)
        else:
            self.metadata_funcs[self.group].append(self.name)

        return fn

    def methods(self):

        return self.metadata_funcs[self.group]