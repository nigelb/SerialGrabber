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

import os, SerialGrabber_Paths, SerialGrabber_Settings
import time
from serial_grabber import cache
from serial_grabber.util import config_helper


class Processor:
    logger = logging.getLogger("Processor")
    def __call__(self, *args, **kwargs):
        try:
            self.logger.info("Processor Thread Started.")
            self.isRunning, self.counter = args
            self.run()
        except BaseException, e:
            self.logger.exception(e)

    def run(self):
        while self.isRunning.running:
            order, c_entries = cache.list_cache()
            if c_entries:
                for entry in order:
                    entry_path = c_entries[entry]
                    if os.path.isfile(entry_path):
                        try:
                                data = {
                                    "data":cache.read_cache(entry_path),
                                    "entry_path": entry_path,
                                    "entry": entry
                                }

                                if self.process(config_helper(data)):
                                    self.counter.posted()
                                    cache.decache(entry_path)
                        except BaseException, e:
                            self.logger.error("Failed to upload data: %s"%e)
                            self.logger.exception(e)
            self.logger.log(5, "Uploader Sleeping.")
            time.sleep(SerialGrabber_Settings.uploader_sleep)

    def process(self, process_entry):
        raise Exception("Reader method \"process\" not implemented.")

class CompositeProcessor(Processor):
    logger = logging.getLogger("CompositeProcessor")

    def __init__(self, processors=()):
        self.processors = processors

    def process(self, process_entry):
        toRet = False
        for pcs in self.processors:
            v = pcs.process(process_entry)
            if v is None: v = False
            toRet |= v
        return toRet

class TransformCompositeProcessor(CompositeProcessor):
    logger = logging.getLogger("TransformCompositeProcessor")

    def __init__(self, transform, processors=()):
        CompositeProcessor.__init__(self, processors)
        self.transform = transform


    def process(self, process_entry):
        transformed_entry = self.transform.transform(process_entry)
        return CompositeProcessor.process(self, transformed_entry)
