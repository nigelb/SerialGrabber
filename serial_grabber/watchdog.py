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
import time
from ctypes import c_int

import SerialGrabber_Settings

from multiprocessing import Process, Queue, Value

from serial_grabber.util import register_worker_signal_handler


class running:
    def __init__(self, running):
        self.running = running

class counter:
    def __init__(self, si):
        self._read = Value(c_int, 0)
        self._error = Value(c_int, 0)
        self._posted = Value(c_int, 0)
        self._invalid = Value(c_int, 0)
        self.si = si

    def read(self):
        self._read.value += 1

    def error(self):
        self._error.value += 1

    def processed(self):
        self._posted.value += 1

    def invalid(self):
        self._invalid.value += 1

    def update(self):
        self.si.set_tooltip("Read Count: %s, Process Count: %s, Error Count: %s, Invalid Count: %s" % (self._read.value, self._posted.value, self._error.value, self._invalid.value))

class Watchdog:
    logger = logging.getLogger("Watchdog")

    def __init__(self, isRunning):
        self.thread_args = {}
        self.threads = {}
        self.isRunning = isRunning
        self.watchdog_thread = Process(target=self.run)
        self.watchdog_thread.start()

    def start_thread(self, func, args, name):
        self.thread_args[func] = args
        thread = Process(target=func, args=args, name=name)
        thread.start()
        time.sleep(1)
        self.threads[func] = thread


    def join(self):
        for func in self.threads:
            self.threads[func].join()
        # self.watchdog_thread.join()
        self.logger.info("Joined all threads.")


    def run(self):
        self.logger.info("Watchdog started.")
        register_worker_signal_handler(self.logger)
        while self.isRunning.value == 1:
            for func in self.threads:
                thread = self.threads[func]
                if not thread.isAlive():
                    try:
                        name = thread.getName()
                        self.logger.error("The thread: %s has stopped, restarting..."%name)
                        thread.join()
                        thread = Process(target = func, args=self.thread_args[func], name=name)
                        thread.start()
                        self.threads[func] = thread
                        self.logger.info("Started Thread: %s"%name)
                    except:
                        self.logger.error("An error occurred when trying to restart the thread.")
            time.sleep(SerialGrabber_Settings.watchdog_sleep)
        self.logger.info("Shutting Down...")
