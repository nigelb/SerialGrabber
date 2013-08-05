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
import inspect
import dbus
from serial_grabber.commander.AquariumCommander import BUS_NAME, BUS_PATH

from serial_grabber.commander.cgi import create_api_routes, MetaDataAPIHandler, metadata

AQUARIUM_API_ID = "Aquarium"
Route = create_api_routes("Route", AQUARIUM_API_ID)

class AquariumAPI(MetaDataAPIHandler):
    def __init__(self, config):
        MetaDataAPIHandler.__init__(self, config, AQUARIUM_API_ID)

    def encode_results(self, request, results):
        return results


def get_dbus_proxy(method_name):
    bus = dbus.SystemBus()
    service = bus.get_object(BUS_NAME, BUS_PATH)
    return service.get_dbus_method(method_name, BUS_NAME)


@Route("/temp/set(/*)$")
def tempPID_set(request):
    methods = metadata(group="/temp/set").methods()
    m = [x.replace("/temp/set","").replace("temp","").replace("PID_set","") for x in methods]
    return "\n".join(m)

@metadata(group="/temp/set")
@Route("/temp/set/Ki")
def tempPID_setKi(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/temp/set")
@Route("/temp/set/Kp")
def tempPID_setKp(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/temp/set")
@Route("/temp/set/Kd")
def tempPID_setKd(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/temp/set")
@Route("/temp/set/Schedule")
def tempSchedule(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(name="Point", group="/temp/set")
@Route("/temp/set/Point")
def tempPID_setSetPoint(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

###################################################

@Route("/ph/set(/*)$")
def phPID_set(request):
    methods = metadata(group="/ph/set").methods()
    m = [x.replace("/ph/set","").replace("ph","").replace("PID_set","") for x in methods]
    return "\n".join(m)

@metadata(group="/ph/set")
@Route("/ph/set/Kp")
def phPID_setKp(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/ph/set")
@Route("/ph/set/Ki")
def phPID_setKi(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/ph/set")
@Route("/ph/set/Kd")
def phPID_setKd(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(group="/ph/set")
@Route("/ph/set/Schedule")
def phSchedule(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))

@metadata(name="Point", group="/ph/set")
@Route("/ph/set/Point")
def phPID_setSetPoint(request):
    func = get_dbus_proxy(inspect.stack()[0][3])
    return func(float(request.request))