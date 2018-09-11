# !/usr/bin/env python
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

import os, SerialGrabber_Settings
import time
import datetime
from SerialGrabber_Storage import storage_cache
from serial_grabber.transform import DebugTransformException
from serial_grabber.util import config_helper, RollingFilename


class ProcessorManager:
    """
    Runs the processor by reading from the storage and passing the payloads
    to the contained processor.
    """
    logger = logging.getLogger("ProcessorManager")

    def __init__(self, processor):
        self._processor = processor

    def __call__(self, *args, **kwargs):
        """
        Starts the processor thread, passing in the isRunning flag which is used
        for termination
        """
        try:
            self.logger.info("Processor Thread Started.")
            self.isRunning, self.counter, self.parameters = args
            self.run()
        except BaseException, e:
            self.logger.exception(e)

    def run(self):
        while self.isRunning.running:
            order, c_entries = storage_cache.list_cache()
            if c_entries and self._processor.can_process():
                for entry in order:
                    parts = entry.split("-")
                    cache_time = float(parts[0].split(".")[0])
                    current_time = time.mktime(datetime.datetime.now().timetuple())
                    if abs(cache_time - current_time) > SerialGrabber_Settings.cache_collision_avoidance_delay:
                        entry_path = c_entries[entry]
                        if os.path.isfile(entry_path):
                            try:
                                data = {
                                    "data": storage_cache.read_cache(entry_path),
                                    "entry_path": entry_path,
                                    "entry": entry
                                }

                                if self._processor.process(config_helper(data)):
                                    self.counter.processed()
                                    storage_cache.decache(entry_path)
                            except DebugTransformException, de:
                                self.logger.debug("Debug exception: %s" % de)
                            except BaseException, e:
                                self.logger.error("Failed to process data: %s moving to bad data archive" % e)
                                self.logger.exception(e)
                                self.counter.error()
                                storage_cache.decache(entry_path, type="bad_data")
                        else:
                            self.logger.debug("File is to new. Leaving for next round.")
                    if not self.isRunning.running:
                        self.logger.error("Stopped Running during entry iteration, breaking.")
                        break
            self.logger.log(5, "Processor Sleeping.")
            time.sleep(SerialGrabber_Settings.processor_sleep)


class Processor:
    logger = logging.getLogger("Processor")

    def process(self, process_entry):
        """
        Process the entry and returns whether the entry was actually processed
        :return: was entry processed
        :rtype: bool
        """
        raise Exception("Reader method \"process\" not implemented.")

    def can_process(self):
        """
        Some processors can determine weather processing can be accomplished, for example
         do not bother processing if there is no network connectivity.
        :return: can processing be accomplished
        :rtype: bool
        """
        return True


class ExternalFilenameProcessor(Processor):
    def setOutputFileName(self, filename):
        self.filename = filename


class TransactionFilteringProcessor(Processor):
    def setTransactionFilter(self, filter):
        self.filter = filter


class CompositeProcessorIgnoreResult(Exception):
    pass


class IgnoreResultProcessor(Processor):
    def __init__(self, processor):
        self.processor = processor

    def process(self, process_entry):
        try:
            self.processor.process(process_entry)
        finally:
            raise CompositeProcessorIgnoreResult()

    def can_process(self):
        try:
            self.processor.can_process()
        finally:
            raise CompositeProcessorIgnoreResult()


class CompositeProcessor(Processor):
    """
    Allows processing by multiple processors.

    :param processors: The list of Processors.
    :type processors: List of objects that implement serial_grabber.processor.Processor
    :param composition_operation: The function that composes the Processor results, default: ``lambda a, b: a or b``.
    :type composition_operation: lambda a, b
    :param bool starting_value: The initial value passed to the composition_operation with the result from the first processor.
    """
    logger = logging.getLogger("CompositeProcessor")

    def __init__(self, processors=(), composition_operation=lambda a, b: a or b, starting_value=False):
        self.processors = processors
        self.operation = composition_operation
        self.starting_value = starting_value

    def process(self, process_entry):
        toRet = self.starting_value
        for pcs in self.processors:
            try:
                v = pcs.process(process_entry)
                if v is None: v = False
                toRet = self.operation(toRet, v)
            except CompositeProcessorIgnoreResult, e:
                pass
        return toRet

    def can_process(self):
        toRet = self.starting_value
        for pcs in self.processors:
            try:
                v = pcs.can_process()
                if v is None: v = False
                toRet = self.operation(toRet, v)
            except CompositeProcessorIgnoreResult, e:
                pass
        return toRet



class TransformProcessor(Processor):
    """
    Transforms the transaction being processed and passes it to the specified Processor.

    :param transform: The transformation to use
    :type transform: serial_grabber.transform.Transform
    :param processor: The Processor to pass the transformed transaction
    :type processor: serial_grabber.processor.Processor
    """
    logger = logging.getLogger("TransformProcessor")

    def __init__(self, transform, processor):
        self.transform = transform
        self.processor = processor

    def process(self, process_entry):
        transformed_entry = self.transform.transform(process_entry)
        if transformed_entry:
            return self.processor.process(transformed_entry)
        return True

    def can_process(self):
        return self.processor.can_process()


class RollingFilenameProcessor(RollingFilename, Processor):
    """
    Used to change the output filename of processors that implement :py:class:`serial_grabber.processor.ExternalFilenameProcessor`.
    The file names are aligned on *boundary* it rolled forward every *period_ms* with a call to *output_processor.setOutputFileName*
    having the form of:  *output_dir*/*date_time.file_extension*.

    :param int boundary: The boundary on which to align the filename roll on.
    :param int period_ms: The period (in milliseconds) to change the filename on.
    :param string output_dir: The directory to write the output to
    :param string file_extension: The file extension to give the output file.
    :param output_processor: The processor to process the chunk.
    :type output_processor: serial_grabber.processor.ExternalFilenameProcessor
    """

    def __init__(self, boundary, period_ms, output_dir, file_extension, output_processor):
        RollingFilename.__init__(self, boundary, period_ms, file_extension)
        self.output_dir = output_dir
        self.output_processor = output_processor
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def process(self, process_entry):
        __process_entry = config_helper(process_entry)
        op = self.calculate_output_name("{ts}.{ext}", __process_entry.data.time)
        if op != self.out_name:
            self.out_name = op
            self.output_processor.setOutputFileName(os.path.join(self.output_dir, op))
        self.output_processor.process(__process_entry)


class LoggingProcessor(Processor):
    """
    This processor simply logs the payload. Mainly useful for debugging, but
    it returns False, so it can be used to observe a CompositeProcessor
    pipeline.
    """
    logger = logging.getLogger("LoggingProcessor")

    def __init__(self, ack=True):
        """
        :param bool ack: should the entry be acknowledged
        """
        self.ack = ack

    def process(self, process_entry):
        self.logger.info("Got: %s" % str(process_entry))
        return self.ack

# class TransactionFilter:
#     def __init__(self):
#         pass
#
#     def filter(self, transaction):
#         raise Exception("Not implemented")
