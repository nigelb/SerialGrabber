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
from ctypes import c_int

import serial
from multiprocessing import Pipe, Value, Lock

import SerialGrabber_Settings
import struct
from SerialGrabber_Storage import storage_cache as cache
from SerialGrabber_Storage import storage_archive
import time

from serial_grabber.pipe_proxy import expose_object, PipeProxy
from serial_grabber.commander import MultiProcessParameterFactory
from serial_grabber.reader.SerialReader import SerialReader
from serial import SerialException
from xbee import ZigBee
import io
import logging

# This if statement removes errors when building the documentation
if 'api_responses' in ZigBee.__dict__:
    ZigBee.api_responses[b'\xa1'] = {'name': 'route_record_indicator', 'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa2'] = {'name': 'device_authenticated_indicator',
                                     'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa3'] = {'name': 'many_to_one_route_request_indicator',
                                     'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa4'] = {'name': 'register_joining_device_indicator',
                                     'structure': [{'name': 'data', 'len': None}]}
    ZigBee.api_responses[b'\xa5'] = {'name': 'join_notification_status', 'structure': [{'name': 'data', 'len': None}]}


class DigiRadioReader(SerialReader):
    logger = logging.getLogger('DigiRadioReader')

    def __init__(self, serial_connection,
                 radio_class=ZigBee,
                 packet_filter=lambda a: True, **kwargs):
        SerialReader.__init__(self, None, 0, serial_connection)
        self.radio_class = radio_class
        self.radio_args = kwargs
        self.packet_filter = packet_filter

    # http://code.google.com/p/python-xbee/
    def run(self):
        # config = config_helper({})
        # config.counter = self.counter
        self.radio = None
        while self.isRunning.value == 1:
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
                print "Really dead", str(se)
                return
            except Exception, e:
                self.counter.error()
                import traceback

                traceback.print_exc()
            if self.stream is None:
                time.sleep(SerialGrabber_Settings.reader_error_sleep)

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

        def error_callback(e):
            self.logger.exception("Exception from radio: %s" % str(e))

        self.radio._error_callback = error_callback

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


class MessageVerifier:
    """
    A is passed to a StreamRadioReader. Each transaction extracted by the Transaction extractor is
    passed to verify_message which validates the message and returns a response to be sent back
    over the radio.
    """
    def __init__(self, ack=None):
        self.ack = ack

    def verify_message(self, transaction):
        return True, self.ack


class ResponseHandler:
    def handle_response_frame(self, frame):
        raise NotImplementedError()


class StreamRadioReader(DigiRadioReader, MultiProcessParameterFactory):
    """
    Reads Digi Xbee/ZigBee API mode packets from the configured serial port, converts the packets into a stream for each MAC Address and passes the stream onto a :py:class:`serial.grabber.reader.TransactionExtractor`

    :param stream_transaction_factory: The function that creates a :py:class:`serial.grabber.reader.TransactionExtractor`
        with the specified stream_id
    :type stream_transaction_factory: fn(stream_id)
    :param SerialConnection serial_connection: A serial connection object
    :param radio_class: The implementation to use, eg: xbee.zigbee.ZigBee
    :type radio_class: xbee.base.XBeeBase
    :param packet_filter: A function that takes one parameter, the parsed radio packet, and returns a bool specifying
       weather or not to keep the packet.
    :type packet_filter: lambda a: True
    :param binary: Weather the data recieved needs to be base64 encoded by the cache (otherwise binary data may mess up the cache json)
    :param bool escaped: The radio is in API mode 2
    """

    def __init__(self,
                 stream_transaction_factory,
                 serial_connection,
                 message_verifier=MessageVerifier(),
                 radio_class=ZigBee,
                 packet_filter=lambda a: True,
                 binary=True, **kwargs):
        DigiRadioReader.__init__(self, serial_connection, radio_class,
                                 packet_filter, **kwargs)
        self.message_verifier = message_verifier
        self.stream_transaction_factory = stream_transaction_factory
        self.streams = {}
        self.short_address = {}
        self.binary = binary

    def handle_frame(self, frame):
        if frame['id'] == 'rx':
            self.short_address[frame['source_addr_long']] = frame['source_addr']
            if frame['source_addr_long'] not in self.streams:
                self.streams[frame['source_addr_long']] = self.stream_transaction_factory(frame['source_addr_long'])
                self.streams[frame['source_addr_long']].set_callback(
                    lambda stream_id, transaction: self.handle_transaction(stream_id, transaction))
            self.streams[frame['source_addr_long']].write(frame['rf_data'])
        else:
            self.logger.info(frame)
            if frame['id'] == 'tx_status':
                for hndlr in self.response_handlers:
                    hndlr.handle_response_frame({
                        'response_id': frame['frame_id'],
                        'status': frame['deliver_status'] == '\x00',
                        'retries': struct.unpack('B', frame['retries'])[0]
                    })


    def handle_transaction(self, stream_id, transaction):
        try:
            isValid, response = self.message_verifier.verify_message(transaction)
            entry = cache.make_payload(transaction, binary=self.binary)
            entry['stream_id'] = " ".join([format(ord(x), "02x") for x in stream_id])
            path = cache.cache(entry)
            if isValid:
                self.counter.read()
                self.counter.update()
            else:
                storage_archive.archive(path, name="invalid")
                self.counter.invalid()
                self.counter.update()

            dest_addr = self.short_address[stream_id]
            self.radio.send("tx", dest_addr_long=stream_id, dest_addr=dest_addr, data=response)


        except Exception, e:
            self.logger.exception("Error handling transaction from: %s %%s" % stream_id, e)

    def setup(self):
        DigiRadioReader.setup(self)

    def setup_command_stream(self):
        self.xbee_stream = XBeeStream(self)
        expose_object(self.parameters['command_stream'][0], self.xbee_stream)
        self.response_handlers = []
        for resp_hdlr in self.parameters.send_response_observers:
            self.response_handlers.append(PipeProxy(resp_hdlr))


def populate_parameters(self, paramaters):
        paramaters.command_stream = Pipe()
        paramaters.command_type = XBeeStream

class XBeeStream:

    auto_ack = False

    def __init__(self, reader):
        self.reader = reader
        self.lock = Lock()
        self.ids = range(10, 256)
        self.pos = 0

    def write(self, data, stream_id="FF FF FF FF FF FF FF", response_id='\x01'):
        address = []
        for i in stream_id.split(" "):
            address.append(int(i, 16))
        address = struct.pack("BBBBBBBB", *address)
        self.reader.radio.send("tx", dest_addr='\xff\xfe', dest_addr_long=address, frame_id=response_id, data=data.encode("ascii"))

    def get_next_idenifier(self):
        self.lock.acquire()
        ps = self.pos
        self.pos = (self.pos + 1) % len(self.ids)
        self.lock.release()
        return struct.pack("B", self.ids[ps])


    def __str__(self):
        return 'XBeeStream'
