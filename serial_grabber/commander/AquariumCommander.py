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

import dbus

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
from serial_grabber.commander import Commander
import setproctitle


BUS_NAME = "serial_grabber.Aquarium"
BUS_PATH = '/serial_grabber/Aquarium'

class Aquarium(dbus.service.Object, Commander):
    dbus_loop = DBusGMainLoop(set_as_default=True)
    logger = logging.getLogger("AquariumCommander")
    def __init__(self):
        bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SystemBus(mainloop=self.dbus_loop))
        dbus.service.Object.__init__(self, bus_name, BUS_PATH)
        self.loop = gobject.MainLoop()
        self.temp_pid = "temp_pid set"
        self.ph_pid = "ph_pid set"

    def __call__(self, *args, **kwargs):
        self.logger.info("Started Aquarium Commander")
        self.isRunning, self.counter, self.stream = args
        setproctitle.setproctitle("%s - AquariumCommander"%setproctitle.getproctitle())
        gobject.threads_init()
        self.loop.run()


    @dbus.service.method(BUS_NAME)
    def tempPID_setKp(self, Kp):
        command = [self.temp_pid, "Kp", str(Kp)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def tempPID_setKi(self, Ki):
        command = [self.temp_pid, "Ki", str(Ki)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def tempPID_setKd(self, Kd):
        command = [self.temp_pid, "Kd", str(Kd)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def tempPID_setSetPoint(self, setPoint):
        command = [self.temp_pid, "point", str(setPoint)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def tempSchedule(self, schedule):
        return "OK"

    @dbus.service.method(BUS_NAME)
    def phPID_setKp(self, Kp):
        command = [self.ph_pid, "Kp", str(Kp)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def phPID_setKi(self, Ki):
        command = [self.ph_pid, "Ki", str(Ki)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def phPID_setKd(self, Kd):
        command = [self.ph_pid, "Kd", str(Kd)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def phPID_setSetPoint(self, setPoint):
        command = [self.ph_pid, "point", str(setPoint)]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        return " ".join(command)

    @dbus.service.method(BUS_NAME)
    def phSchedule(self, schedule):
        return "OK"

    def stop(self):
        self.loop.quit()




