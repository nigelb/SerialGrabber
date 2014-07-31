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

import serial
import SerialGrabber_Settings
import time
from serial_grabber import cache
from serial_grabber.reader.SerialReader import SerialReader
from serial_grabber.util import config_helper, get_millis
from serial import SerialException
from xbee import ZigBee

#This if statement removes errors when building the documentation
if 'api_responses' in ZigBee.__dict__:
    ZigBee.api_responses[b'\xa1'] = {'name': 'route_record_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa2'] = {'name': 'device_authenticated_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa3'] = {'name': 'many_to_one_route_request_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa4'] = {'name': 'register_joining_device_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa5'] = {'name': 'join_notification_status', 'structure': [{'name': 'data', 'len': None}]}

class DigiRadioReader(SerialReader):
    """
    Reads Digi Xbee/ZigBee API mode packets from the configured serial port

    :param str port: The serial port to use, eg: /dev/ttyUSB0
    :param int baud: The baud rate to use, eg: 115200
    :param int timeout: eg: 60
    :param int parity: eg: serial.PARITY_NONE
    :param int stop_bits: eg: serial.STOPBITS_ONE
    :param radio_class: The implementation to use, eg: xbee.zigbee.ZigBee
    :type radio_class: xbee.base.XBeeBase
    :param packet_filter: A function that takes one parameter, the parsed radio packet, and returns a bool specifying
       weather or not to keep the packet.
    :type packet_filter: lambda a: True
    :param bool escaped: The radio is in API mode 2
    """
    def __init__(self, port, baud,
                 timeout=60,
                 parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE,
                 radio_class=ZigBee,
                 packet_filter=lambda a: True, **kwargs):
        SerialReader.__init__(self, port, baud, timeout, parity, stop_bits)
        self.radio_class = radio_class
        self.radio_args = kwargs
        self.packet_filter = packet_filter

    # http://code.google.com/p/python-xbee/
    def run(self):
        config = config_helper({})
        config.counter = self.counter
        self.radio = None
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    self.radio = self.radio_class(self.stream, **self.radio_args)
                    continue
                response = self.radio.wait_read_frame()
                if response is None:
                    self.logger.error("There was an error reading")
                else:
                    if self.packet_filter(response):
                        cache.cache(cache.make_payload(response, binary=True))
                        config.counter.read()
                        config.counter.update()
                    else:
                        self.logger.info("Packet dropped by packet filter.")

            except SerialException, se:
                self.close()
                return
            except Exception, e:
                self.counter.error()
                import traceback

                traceback.print_exc()
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)
