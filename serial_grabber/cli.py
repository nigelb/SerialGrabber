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

from serial_grabber.watchdog import running, counter, Watchdog

class status:
    def __init__(self, logger):
        self.logger = logger

    def set_tooltip(self, tooltip):
        self.logger.info(tooltip)

def start(logger, run_reader, run_poster):
    si = status(logger)
    isRunning = running(True)
    c = counter(si)
    #    reader = Thread(target=run_reader, args=(isRunning, c))
    #    poster = Thread(target=run_poster, args=(isRunning, c))
    #    reader.start()
    #    poster.start()
    watchdog = Watchdog(isRunning)
    watchdog.start_thread(run_reader, (isRunning, c), "Runner")
    watchdog.start_thread(run_poster, (isRunning, c), "Uploader")
