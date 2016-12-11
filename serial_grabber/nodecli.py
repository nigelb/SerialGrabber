import argparse
import sys
import paho.mqtt.client as mqtt
import datetime
import json
import threading


class MqttClient(object):
    def __init__(self, host, port, auth, master_topic="master/maintenance",
                 data_topic="master/data"):
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

        self._stopping = threading.Event()

    def connect(self):
        """
        Connect to the message bus
        """
        self._con.connect(self._mqtt_host, self._mqtt_port)

    def listen(self):
        self.connect()
        self._con.subscribe(self._master_topic)
        self._con.subscribe(self._data_topic)
        self._stopping.clear()
        while not self._stopping.isSet():
            self._con.loop()

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

    def _print_message(self, payload):
        payload = json.loads(payload)

        self._print(str(payload))

    def _print_data(self, payload):
        payload = json.loads(payload)
        msg = "Got data from %(nodeIdentifier)s with timestamp %(timestamp)s\n"
        msg = msg % payload
        for line in payload['data'].split('\n'):
            msg += '\t%s\n' % line
        self._print(msg)


def main():
    parser = argparse.ArgumentParser("node command line interface")
    parser.add_argument('mqtt_host', help="MQTT host name")
    parser.add_argument('-P', help="MQTT port", type=int, default=1883)
    parser.add_argument('-u', help="MQTT username")
    parser.add_argument('-p', help="MQTT password")
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('listen', help="Listen for messages from the buoy")

    args = parser.parse_args()

    con = MqttClient(args.mqtt_host, args.P, (args.u, args.p))

    if args.action == 'listen':
        con.listen()

    return 0

if __name__ == '__main__':
    sys.exit(main())
