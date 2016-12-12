import argparse
import sys
import paho.mqtt.client as mqtt
import datetime
import json
import threading


class MqttClient(object):
    def __init__(self, host, port, auth, master_topic="master/maintenance",
                 data_topic="master/data", node_topic='nodes'):
        """
        Create the MQTT connection.
        :param:str host:MQTT host
        :param:int port:MQTT port
        :param:tuple auth:tuple of (username, password)
        """
        self._con = mqtt.Client()
        if auth is not None and len(auth) == 2 and auth[0] is not None:
            self._con.username_pw_set(auth[0], auth[1])

        self._con.on_connect = self._on_connect
        self._con.on_message = self._on_message

        self._mqtt_host = host
        self._mqtt_port = port
        self._master_topic = master_topic
        self._data_topic = data_topic
        self._node_topic = node_topic

        self._stopping = threading.Event()

    def _connect(self):
        """
        Connect to the message bus
        """
        self._con.connect(self._mqtt_host, self._mqtt_port)

    def _disconnect(self):
        self._con.disconnect()

    def _print(self, msg):
        print "At " + datetime.datetime.now().strftime('%H:%M:%S')
        print msg
        print

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._print("Connected to message bus")
        elif rc == 1:
            self._print("Connection to message bus failed: "
                        "incorrect protocol version")
        elif rc == 2:
            self._print("Connection to message bus failed: "
                        "invalid client identifier")
        elif rc == 3:
            self._print("Connection to message bus failed: "
                        "server unavailable")
        elif rc == 4:
            self._print("Connection to message bus failed: "
                        "bad username or password")
        elif rc == 5:
            self._print("Connection to message bus failed: "
                        "not authorised")

        if rc != 0:
            self._stopping.set()

    def _on_message(self, client, userdata, msg):
        if msg.topic == self._master_topic:
            self._print_message(msg.payload)
        elif msg.topic == self._data_topic:
            self._print_data(msg.payload)
        else:
            self._print("Got stray message on " + msg.topic)

    def _print_success(self, operation, success):
        if success:
            print "FAILED TO: " + operation
        else:
            print "SUCCEEDED: " + operation

    def _print_message(self, payload):
        payload = json.loads(payload)
        if 'response' in payload:
            msg = "Got response to %(response)s from %(nodeIdentifier)s with timestamp %(timestamp)s\n"
        else:
            msg = "Got notification of %(notify)s from %(nodeIdentifier)s with timestamp %(timestamp)s\n"

        msg = msg % payload

        for part in payload['body']:
            msg += '\t%s=%s\n' % (part, str(payload['body'][part]))

        self._print(msg)

    def _print_data(self, payload):
        """
        Formats and prints a data payload
        """
        payload = json.loads(payload)
        msg = "Got data from %(nodeIdentifier)s with timestamp %(timestamp)s\n"
        msg = msg % payload
        for line in payload['data'].split('\n'):
            msg += '\t%s\n' % line
        self._print(msg)

    def _send_broadcast(self, operation, cmd):
        """
        Sends a broadcast command and prints the success of the send
        """
        self._connect()
        m = self._con.publish(self._node_topic,
                              json.dumps(cmd), 2)
        self._disconnect()
        self._print_success(operation,
                            m.is_published())

    def _send_to_node(self, operation, node_identifier, cmd):
        """
        Sends a command to a node, and the prints the success of the send
        """
        self._connect()
        m = self._con.publish(self._node_topic + '/' + node_identifier,
                              json.dumps(cmd), 2)
        self._disconnect()
        self._print_success(operation,
                            m.is_published())

    def listen(self):
        """
        Listen to incoming messages from the nodes
        """
        self._connect()
        self._con.subscribe(self._master_topic)
        self._con.subscribe(self._data_topic)
        self._stopping.clear()
        while not self._stopping.isSet():
            self._con.loop()

    def cmd_ping(self):
        """
        Issues the mode change command to a node
        """
        cmd = {'request': 'ping'}
        self._send_broadcast('Send ping', cmd)

    def cmd_mode(self, node_identifier, mode):
        """
        Issues the mode change command to a node
        """
        cmd = {'request': 'mode', 'mode': mode}
        self._send_to_node("Send mode change to %s" % node_identifier,
                           node_identifier, cmd)


def main():
    parser = argparse.ArgumentParser("node command line interface")
    parser.add_argument('mqtt_host', help="MQTT host name")
    parser.add_argument('-P', help="MQTT port", type=int, default=1883)
    parser.add_argument('-u', help="MQTT username")
    parser.add_argument('-p', help="MQTT password")
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('listen', help="Listen for messages from the buoy")
    subparsers.add_parser('ping', help="Issue a broadcast ping")
    mode_parser = subparsers.add_parser('mode', help="Perform a mode change")
    mode_parser.add_argument('node_identifier')
    mode_parser.add_argument('mode')

    args = parser.parse_args()

    con = MqttClient(args.mqtt_host, args.P, (args.u, args.p))

    if args.action == 'listen':
        con.listen()
    elif args.action == 'ping':
        con.cmd_ping()
    elif args.action == 'mode':
        con.cmd_mode(args.node_identifier, args.mode)

    return 0

if __name__ == '__main__':
    sys.exit(main())
