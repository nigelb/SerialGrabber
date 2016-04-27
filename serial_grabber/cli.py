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
import signal
import time

from SerialGrabber_Storage import storage_cache
from ctypes import c_int
from multiprocessing import Process, Queue, Value
from serial_grabber.commander import MultiProcessParameterFactory
from serial_grabber.util import config_helper


from serial_grabber.watchdog import running, counter, Watchdog

from serial_grabber.processor import ProcessorManager

class status:
    def __init__(self, logger):
        self.logger = logger

    def set_tooltip(self, tooltip):
        self.logger.info(tooltip)

def register_handler(running, watchdog, reader, processor, command):
    def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        running.value = 0
        if command:
            command.stop()
        watchdog.join()
        if reader:
            reader.close()


        exit(0)
    signal.signal(signal.SIGINT, signal_handler)

def start(logger, reader, processor, command):
    try:
        si = status(logger)
        # isRunning = running(True)
        isRunning = Value(c_int, 1)

        c = counter(si)

        params = config_helper({
            "counter": c,
            "running": isRunning
        })

        if issubclass(command.__class__, MultiProcessParameterFactory):
            command.populate_parameters(params)
        if issubclass(reader.__class__, MultiProcessParameterFactory):
            reader.populate_parameters(params)
        if issubclass(processor.__class__, MultiProcessParameterFactory):
            processor.populate_parameters(params)

        watchdog = Watchdog(isRunning)

        if reader:
            watchdog.start_thread(reader, (isRunning, c, params), "Runner")
        if processor:
            watchdog.start_thread(ProcessorManager(processor), (isRunning, c, params), "Processor")
        if command and reader:
            watchdog.start_thread(command, (isRunning, c, params), "Commander")
        register_handler(isRunning, watchdog, reader, processor, command)
        while isRunning.value == 1:
            time.sleep(1)
    finally:
        storage_cache.close_cache()
