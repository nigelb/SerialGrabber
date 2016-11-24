# !/usr/bin/env python
# SerialGrabber reads data from a serial port and processes it with the
# configured processor.
# Copyright (C) 2016  NigelB, NigelS
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

from serial_grabber.commander import Commander
from serial_grabber.processor import Processor
import paho.mqtt.client as mqtt


class MqttCommander(Commander):

    logger = logging.getLogger("MqttCommander")

    def __init__(self, host, port, auth, master_topic="master",
                 nodes_topic="nodes"):
        # Setup the basic MQTT config
        self._mqtt = mqtt.Client()
        self._mqtt.username_pw_set(auth[0], auth[1])
        self._mqtt.on_connect = self.on_connect
        self._mqtt.on_message = on_message

        self._mqtt_host = host
        self._mqtt_port = port

        self._master_topic = master_topic
        self._nodes_topic = nodes_topic

        self.processor = MqttProcessor(self)

    def __call__(self, *args, **kwargs):
        """
        Starts the processor thread, passing in the isRunning flag which is used
        for termination, and the command stream
        """
        try:
            self.logger.info("Commander Thread Started.")
            self.isRunning, self.counter, self.command = args
            self.run()
        except BaseException, e:
            self.logger.exception(e)

    def run(self):
        self._mqtt.connect(self._mqtt_host, self._mqtt_port)
        while self.isRunning.running:
            self._mqtt.loop()
        self._mqtt.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        """
        Handle MQTT connection events
        """
        if rc == 0:
            self.logger.info("Connected to message bus")
            self._mqtt.publish(self._master_topic, 'HELLO')
        elif rc == 1:
            self.logger.warn("Connection to message bus failed: "
                             "incorrect protocol version")
        elif rc == 2:
            self.logger.warn("Connection to message bus failed: "
                             "invalid client identifier")
        elif rc == 3:
            self.logger.warn("Connection to message bus failed: "
                             "server unavailable")
        elif rc == 4:
            self.logger.warn("Connection to message bus failed: "
                             "bad username or password")
        elif rc == 5:
            self.logger.warn("Connection to message bus failed: "
                             "not authorised")

    def on_message(self, client, userdata, msg):
        """
        Handle MQTT messages
        """
        self.logger.info("Got message from %s" % (msg.topic))


class MqttProcessor(Processor):
    """
    This processor intercepts response messages and passes them to the MQTT
    Commander to send on the message bus. Other messages are ignored, and
    should be dealt with by another processor
    """

    def __init__(self, mqtt_commander):
        self._commander = mqtt_commander

    def process(self, process_entry):
        """
        Process the entry and check if it is a response
        """
        return False
