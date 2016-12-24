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
from Verifier import MessageVerifier
from constants import run_types
from serial_grabber.extractors import TransactionExtractor
from serial_grabber.reader.SerialReader import SerialReader
from serial_grabber.connections import TcpServer
from serial_grabber.processor import LoggingProcessor, CompositeProcessor, IgnoreResultProcessor
from serial_grabber.mqtt import MqttCommander

# Serial Settings
hostname = "127.0.0.1"
port = 8099

# MQTT settings
mqtt_host = "localhost"
mqtt_port = 1883
mqtt_auth = ('system', 'manager')


# Settings
cache_collision_avoidance_delay = 1
processor_sleep = 0.1
watchdog_sleep = 1

commander_error_sleep = 1
reader_error_sleep = 1

drop_carriage_return = True

transaction = TransactionExtractor("default", "BEGIN", "END")

tcp = TcpServer(hostname, port)

reader = SerialReader(transaction, 1000, tcp, message_verifier=MessageVerifier())

commander = MqttCommander(mqtt_host, mqtt_port, mqtt_auth, send_data=True)

logging_processor = IgnoreResultProcessor(LoggingProcessor())

processor = CompositeProcessor([commander.processor, logging_processor])

threading_model = run_types.miltiprocessing