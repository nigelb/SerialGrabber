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
import time
from serial_grabber.commander import Commander
from serial_grabber.constants import current_matcher


BUS_NAME = "serial_grabber.Aquarium"
BUS_PATH = '/serial_grabber/Aquarium'

AQUARIUM_CLI_ERROR_PATTERN = "#Error Command Not Found:(.*)"
AQUARIUM_CLI_CALIBRATION_PATTERN="#ph_cal(.*)"

class Aquarium(dbus.service.Object, Commander):
    dbus_loop = DBusGMainLoop(set_as_default=True)
    logger = logging.getLogger("AquariumCommander")
    def __init__(self):
        bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SystemBus(mainloop=self.dbus_loop))
        dbus.service.Object.__init__(self, bus_name, BUS_PATH)
        self.loop = gobject.MainLoop()
        self.temp_pid = "temp_pid set"
        self.ph_pid = "ph_pid set"
        self.ph_cal = "ph_cal"
        self.currently_calibrating = False
        def handler(error):
            self.handle_cli_error(error)
        register_cli_error_handler(handler)

        def _handler(error):
            self.handle_calibration(error)
        register_calibration_handler(_handler)

    def __call__(self, *args, **kwargs):
        self.logger.info("Started Aquarium Commander")
        self.isRunning, self.counter, self.stream = args
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

    @dbus.service.method(BUS_NAME)
    def phCalibration_Low(self):
        return self.phCalibration("low")

    @dbus.service.method(BUS_NAME)
    def phCalibration_Neutral(self):
        return self.phCalibration("neutral")
    @dbus.service.method(BUS_NAME)

    def phCalibration_High(self):
        return self.phCalibration("high")

    def phCalibration(self, type):
        start = time.time()
        if "type" in self.__dict__:
            del self.type
        if self.currently_calibrating:
            return "ERROR: Already Calibrating"
        self.type = type
        self.currently_calibrating = True
        command = [self.ph_cal, type]
        self.stream.write(" ".join(command))
        self.stream.write("\n")
        while (not hasattr(self, 'calibration_result')) and time.time() - start < 200:
            time.sleep(0.5)
        if not hasattr(self, 'calibration_result'):
            self.currently_calibrating = False
            return "TIMEOUT"
        result = self.calibration_result
        del self.calibration_result
        self.currently_calibrating = False
        return result

    def stop(self):
        self.loop.quit()

    def handle_cli_error(self, error):
        print error

    def handle_calibration(self, error):
        type, result = error.split(":")
        if self.currently_calibrating and type == self.type:
            self.calibration_result = result
        else:
            self.calibration_result = None



cli_error_handlers = []
calibration_handlers = []

def register_cli_error_handler(handler):
    cli_error_handlers.append(handler)

def remove_cli_error_handler(handler):
    cli_error_handlers.remove(handler)

def register_calibration_handler(handler):
    calibration_handlers.append(handler)

def aquarium_commander_cli_error_handler(handler_state):
    def cli_error_handler(state, config, data):
        for handler in cli_error_handlers:
            handler(state[current_matcher].group(1).strip())
    return cli_error_handler

def aquarium_commander_calibration_handler(handler_state):
    def calibration_handler(state, config, data):
        for calH in calibration_handlers:
            calH(state[current_matcher].group(1).strip())
    return calibration_handler