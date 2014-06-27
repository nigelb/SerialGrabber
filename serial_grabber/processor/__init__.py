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
import datetime
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
                    parts = entry.split("-")
                    cache_time = float(parts[0].split(".")[0])
                    current_time = time.mktime(datetime.datetime.now().timetuple())
                    if abs(cache_time - current_time) > SerialGrabber_Settings.uploader_collision_avoidance_delay:
                        entry_path = c_entries[entry]
                        if os.path.isfile(entry_path):
                            try:
                                    data = {
                                        "data":cache.read_cache(entry_path),
                                        "entry_path": entry_path,
                                        "entry": entry
                                    }

                                    if self.process(config_helper(data)):
                                        self.counter.processed()
                                        cache.decache(entry_path)
                            except BaseException, e:
                                self.logger.error("Failed to process data: %s moving to bad data archive"%e)
                                self.logger.exception(e)
                                self.counter.error()
                                cache.decache(entry_path, type="bad_data")
                        else:
                            self.logger.debug("File is to new. Leaving for next round.")
                    if not self.isRunning.running:
                        self.logger.error("Stopped Running during entry iteration, breaking.")
                        break
            self.logger.log(5, "Processor Sleeping.")
            time.sleep(SerialGrabber_Settings.uploader_sleep)

    def process(self, process_entry):
        raise Exception("Reader method \"process\" not implemented.")

class ExternalFilenameProcessor(Processor):
    def setOutputFileName(self, filename):
        self.filename = filename

class CompositeProcessor(Processor):
    logger = logging.getLogger("CompositeProcessor")

    def __init__(self, processors=(), composition_operation=lambda a, b: a or b):
        self.processors = processors
        self.operation = composition_operation

    def process(self, process_entry):
        toRet = False
        for pcs in self.processors:
            v = pcs.process(process_entry)
            if v is None: v = False
            toRet = self.operation(toRet, v)
        return toRet

class TransformCompositeProcessor(CompositeProcessor):
    logger = logging.getLogger("TransformCompositeProcessor")

    def __init__(self, transform, processors=()):
        CompositeProcessor.__init__(self, processors)
        self.transform = transform


    def process(self, process_entry):
        transformed_entry = self.transform.transform(process_entry)
        if transformed_entry:
            return CompositeProcessor.process(self, transformed_entry)
        return True

class ChunkingProcessor(Processor):
    def __init__(self, boundary, chunk_size, output_dir, output_processor):
        self.output_dir = output_dir
        self.output_processor = output_processor
        self.boundary = boundary
        self.chunk_size = chunk_size
        self.out_name = None
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def process(self, process_entry):
        __process_entry = config_helper(process_entry)
        op = self.calculate_output_name(__process_entry.data.time)
        if op != self.out_name:
            self.out_name = op
            self.output_processor.setOutputFileName(os.path.join(self.output_dir, op))
        self.output_processor.process(__process_entry)

    def calculate_output_name(self, ts):
        v =  (int((ts - self.boundary) / self.chunk_size) * self.chunk_size) + self.boundary
        return "%s.csv"%v