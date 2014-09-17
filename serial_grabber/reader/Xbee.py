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
from SerialGrabber_Storage import storage_cache as cache
import time
from serial_grabber.reader import TransactionExtractor
from serial_grabber.reader.SerialReader import SerialReader
from serial import SerialException
from xbee import ZigBee
import io

# This if statement removes errors when building the documentation
if 'api_responses' in ZigBee.__dict__:
    ZigBee.api_responses[b'\xa1'] = {'name': 'route_record_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa2'] = {'name': 'device_authenticated_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa3'] = {'name': 'many_to_one_route_request_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa4'] = {'name': 'register_joining_device_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa5'] = {'name': 'join_notification_status', 'structure': [{'name': 'data', 'len': None}]}


class DigiRadioReader(SerialReader):

    def __init__(self, port, baud,
                 timeout=60,
                 parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE,
                 radio_class=ZigBee,
                 packet_filter=lambda a: True, **kwargs):
        SerialReader.__init__(self, 0, port, baud, timeout, parity, stop_bits)
        self.radio_class = radio_class
        self.radio_args = kwargs
        self.packet_filter = packet_filter

    # http://code.google.com/p/python-xbee/
    def run(self):
        # config = config_helper({})
        # config.counter = self.counter
        self.radio = None
        while self.isRunning.running:
            try:
                if self.radio is None:
                    self.setup()
                    continue
                else:
                    if not self.radio.isAlive():
                        self.radio = None
                time.sleep(1)
            except SerialException, se:
                self.close()

                return
            except Exception, e:
                self.counter.error()
                import traceback

                traceback.print_exc()
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)

    def setup(self):
        SerialReader.setup(self)
        if 'callback' in self.radio_args:
            cb = self.radio_args['callback']
            del self.radio_args['callback']
        else:
            cb = lambda frame: self.handle_frame(frame)
        self.radio = self.radio_class(self.stream, **self.radio_args)

        def filtered_callback(frame):
            if self.packet_filter(frame):
                cb(frame)

        self.radio._callback = filtered_callback
        self.radio._thread_continue = True
        self.radio.setDaemon(True)
        self.radio.start()
        self.radio.send("at", command="AI")

    def close(self):
        SerialReader.close(self)
        self.radio._thread_continue = False
        self.radio = None

    def handle_frame(self, frame):
        raise Exception("Not implemented.")


class PacketRadioReader(DigiRadioReader):
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

    def handle_frame(self, response):
        if response is None:
            self.logger.error("There was an error reading")
        else:
            if self.packet_filter(response):
                cache.cache(cache.make_payload(response, binary=True))
                self.counter.read()
                self.counter.update()
            else:
                self.logger.info("Packet dropped by packet filter.")


class StreamRadioReader(DigiRadioReader):
    """
    Reads Digi Xbee/ZigBee API mode packets from the configured serial port, converts the packets into a stream for each
     MAC Address and passes the stream onto a :py:class:`serial.grabber.reader.TransactionExtractor`

    :param stream_transaction_factory: The function that creates a :py:class:`serial.grabber.reader.TransactionExtractor`
        with the specified stream_id
    :type stream_transaction_factory: fn(stream_id)
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
    def __init__(self,
                 stream_transaction_factory,
                 port,
                 baud,
                 timeout=60,
                 parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE,
                 radio_class=ZigBee, packet_filter=lambda a: True, ack=None, **kwargs):
        DigiRadioReader.__init__(self, port, baud, timeout, parity, stop_bits, radio_class, packet_filter, **kwargs)
        self.stream_transaction_factory = stream_transaction_factory
        self.streams = {}
        self.short_address = {}
        self.ack = ack

    def handle_frame(self, frame):
        if frame['id'] == 'rx':
            self.short_address[frame['source_addr_long']] = frame['source_addr']
            if frame['source_addr_long'] not in self.streams:
                self.streams[frame['source_addr_long']] = self.stream_transaction_factory(frame['source_addr_long'])
                self.streams[frame['source_addr_long']].set_callback(
                    lambda stream_id, transaction: self.handle_transaction(stream_id, transaction))
            self.streams[frame['source_addr_long']].write(frame['rf_data'])
        else:
            print frame

    def handle_transaction(self, stream_id, transaction):
        try:
            print " ".join([format(ord(x), "02x") for x in transaction])
            entry = cache.make_payload(transaction, binary=True)
            entry['stream_id'] = " ".join([format(ord(x), "02x") for x in stream_id])
            cache.cache(entry)
            self.counter.read()
            self.counter.update()
            if self.ack:
                dest_addr = self.short_address[stream_id]
                print " ".join([format(ord(x), "02x") for x in stream_id])
                self.radio.send("tx", dest_addr_long=stream_id, dest_addr=dest_addr, data=self.ack)
        except Exception, e:
            self.logger.exception("Error handling transaction from: %s %%s" % stream_id, e)
