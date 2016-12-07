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
import datetime
import json

from serial_grabber.commander import Commander
from serial_grabber.processor import Processor
import paho.mqtt.client as mqtt


class MqttCommander(Commander):

    logger = logging.getLogger("MqttCommander")

    def __init__(self, host, port, auth, master_topic="maintenance",
                 nodes_topic="nodes", data_topic="data", send_data=False,
                 platform_identifier='default_platform'):
        # Setup the basic MQTT config
        self._mqtt = mqtt.Client()
        self._mqtt.username_pw_set(auth[0], auth[1])
        self._mqtt.on_connect = self.on_connect
        self._mqtt.on_message = self.on_message

        self._mqtt_host = host
        self._mqtt_port = port

        self._master_topic = master_topic
        self._nodes_topic = nodes_topic
        self._data_topic = data_topic

        self._platform_identifier = platform_identifier

        self.processor = MqttProcessor(self, send_data)

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
        self._node_identifiers = {}
        self._mqtt.connect(self._mqtt_host, self._mqtt_port)
        self._mqtt.subscribe(self._nodes_topic)
        self._mqtt.subscribe(self._nodes_topic + '/#')
        while self.isRunning.running:
            self._mqtt.loop()
        self._mqtt.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        """
        Handle MQTT connection events
        """
        if rc == 0:
            self.logger.info("Connected to message bus")
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
        if msg.topic == self._nodes_topic:
            # Broadcast
            direct = False
        elif msg.topic.startswith(self._nodes_topic):
            # Direct message
            direct = True
        payload = json.loads(msg.payload)
        # dispatch
        getattr(self, '_cmd_' + payload['request'])(msg.topic, payload, direct)

    def _cmd_ping(self, topic, payload, direct):
        nodes = []
        for stream_id in self._node_identifiers:
            nodes.append({'nodeIdentifier': self._node_identifiers[stream_id]})

        self.send_response(None, datetime.datetime.utcnow(), 'status', nodes)

    def _cmd_mode(self, topic, payload, direct):
        """
        A mode change command. This must be direct
        """
        if not direct:
            self.logger.warn("A non-direct mode change was issued, ignoring")
            return
        _, node_identifier = topic.split('/')

        self.send_to_node(node_identifier, 'MODE %s' % payload['mode'])

    def send_data(self, stream_id, timestamp, data):
        """
        Format and send a data payload for the given data.
        """
        payload = {
            "nodeIdentifier": self._node_identifiers[stream_id],
            "platformIdentifier": self._platform_identifier,
            "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "data": data}
        self._mqtt.publish(self._data_topic, json.dumps(payload))

    def send_notify(self, stream_id, timestamp, notify_type, payload):
        payload = {
            "notify": notify_type,
            "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "platformIdentifier": self._platform_identifier,
            "body": payload
        }
        if stream_id is not None:
            payload["nodeIdentifier"] = self._node_identifiers[stream_id]

        self._mqtt.publish(self._master_topic, json.dumps(payload))

    def send_response(self, stream_id, timestamp, response_type, payload):
        payload = {
            "response": response_type,
            "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "platformIdentifier": self._platform_identifier,
            "body": payload
        }
        if stream_id is not None:
            payload["nodeIdentifier"] = self._node_identifiers[stream_id]

        self._mqtt.publish(self._master_topic, json.dumps(payload))

    def send_to_node(self, node_identifier, payload):
        """
        Send a command to the node. The payload will be wrapped as required.
        """
        payload = """BEGIN
%s
END""" % payload
        stream_id = None
        for stream_id_ in self._node_identifiers:
            if node_identifier == self._node_identifiers[stream_id_]:
                stream_id = stream_id_
                break

        if stream_id is None:
            self.logger.warn("No node identified by %s" % node_identifier)
            return

        self.logger.info("Sending to node %s: %s" % (stream_id, payload))
        self.command().write(payload)

    def update_node_identifier(self, stream_id, node_identifier):
        """
        Updates the current node identifier, which includes
        updating the subscriptions.
        """
        self.logger.info('Node %s on stream %s' % (node_identifier, stream_id))
        self._node_identifiers[stream_id] = node_identifier


class MqttProcessor(Processor):
    """
    This processor intercepts response messages and passes them to the MQTT
    Commander to send on the message bus. Other messages are ignored, and
    should be dealt with by another processor
    """

    def __init__(self, mqtt_commander, send_data):
        self._commander = mqtt_commander
        self._send_data = send_data

    def process(self, entry):
        """
        Process the entry and check if it is a response
        """
        lines = entry['data']['payload'].split('\n')
        ts = datetime.datetime.utcfromtimestamp(entry['data']['time']/1000.0)

        if lines[1] == 'NOTIFY':
            notify_type, data = parse_notify(lines[2])
            if notify_type == 'HELLO':
                # Update the current identifier
                self._commander.update_node_identifier(
                    entry['data']['stream_id'], data['identifier'])

            self._commander.send_notify(entry['data']['stream_id'], ts,
                                        notify_type, data)
            return True
        elif lines[1] == 'RESPONSE':
            notify_type, data = parse_notify(lines[2])
            self._commander.send_response(entry['data']['stream_id'], ts,
                                          notify_type, data)

            return True
        elif self._send_data and lines[1] == 'DATA':
            # send data
            stream_id = entry['data']['stream_id']
            data = entry['data']['payload']
            self._commander.send_data(stream_id, ts, data)
            return True
        else:
            return False


def parse_notify(payload):
    """
    Parse a notify line into a type and a dict of parameters
    """
    ix = payload.find(':')
    notify_type = payload[:ix]
    data = {}
    for p in payload[ix + 1:].split(','):
        p = p.split(':')
        data[p[0].strip()] = p[1].strip()
    return notify_type, data
