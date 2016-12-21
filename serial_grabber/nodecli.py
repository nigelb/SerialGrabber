import argparse
import sys

import multiprocessing
import paho.mqtt.client as mqtt
import datetime
import json
import threading
import time


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
        self.single = True

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
        if 'tx_id' not in payload:
            payload['tx_id'] = ""
        else:
            payload['tx_id'] = "(%s)"%payload['tx_id']
        if 'response' in payload:
            if 'nodeIdentifier' in payload:
                msg = "Got response to %(response)s%(tx_id)s from %(nodeIdentifier)s with timestamp %(timestamp)s\n"
            else:
                msg = "Got response to %(response)s%(tx_id)s with timestamp %(timestamp)s\n"

        else:
            msg = "Got notification of %(notify)s from %(nodeIdentifier)s with timestamp %(timestamp)s\n"

        msg = msg % payload

        if isinstance(payload['body'], dict):
            for part in payload['body']:
                msg += '\t%s=%s\n' % (part, str(payload['body'][part]))
        else:
            msg += '\t%s' % str(payload['body'])

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
        if self.single: self._connect()
        m = self._con.publish(self._node_topic,
                              json.dumps(cmd), 1)
        if self.single: self._disconnect()
        self._print_success(operation,
                            m.is_published())

    def _send_to_node(self, operation, node_identifier, cmd):
        """
        Sends a command to a node, and the prints the success of the send
        """
        if self.single: self._connect()
        m = self._con.publish(self._node_topic + '/' + node_identifier,
                              json.dumps(cmd), 1)
        if self.single: self._disconnect()
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
        tx_id = int(time.time()*1000)
        cmd = {'request': 'mode', 'mode': mode, 'tx_id': tx_id}
        self._send_to_node("Send mode change to %s" % node_identifier,
                           node_identifier, cmd)
        return tx_id

    def ph_3_point_calibration(self, node_identifier, mid, t_mid, high, t_high, low, t_low):
        calibrate = [
            ["mid", mid, t_mid],
            ["high", high, t_high],
            ["low", low, t_low],
        ]
        return self.run_ph_calibration(node_identifier, 3, calibrate)

    def ph_2_point_calibration(self, node_identifier, mid, t_mid, second_point, second_point_ph, second_point_temp):
        calibrate = [
            ["mid", mid, t_mid],
            [second_point, second_point_ph, second_point_temp],
        ]
        return self.run_ph_calibration(node_identifier, 2, calibrate)

    def ph_1_point_calibration(self, node_identifier, mid, t_mid):
        calibrate = [
            ["mid", mid, t_mid],
        ]
        return self.run_ph_calibration(node_identifier, 1, calibrate)

    def run_ph_calibration(self, node_identifier, number_of_points, calibrate):
        self.single = False
        ph_cal = PH_Calibration(node_identifier, number_of_points, calibrate)
        calibration_thread = threading.Thread(
            target= ph_cal,
            args=(self._stopping, self),
            name="PH Calibration")
        calibration_thread.daemon = True
        calibration_thread.start()
        self._con.on_message = ph_cal.on_message
        self.listen()


class Calibration:
    def __init__(self, node_identifier):
        self.node_identifier = node_identifier
        self.message_lock = threading.Lock()
        self.messages = {}

    def __call__(self, *args, **kwargs):
        self._stopping, self.client = args
        time.sleep(1)
        print "Starting PH Calibration Thread"
        self.run()
        print "Calibration complete"
        self._stopping.set()

    def wait_for_response(self, tx_id):
        found = False
        result = None
        while not found:
            self.message_lock.acquire()
            if tx_id in self.messages:
                result = self.messages[tx_id]
                found = True
            self.message_lock.release()
            time.sleep(0.01)
        return result

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload)
        if payload["nodeIdentifier"] == self.node_identifier:
            if 'tx_id' in payload and 'response' in payload:
                self.message_lock.acquire()
                self.messages[int(payload['tx_id'])] = payload
                self.message_lock.release()

    def run(self):
        raise NotImplemented("run is not Implemented...")


class PH_Calibration(Calibration):
    def __init__(self, node_identifier, number_of_points, calibrate):
        Calibration.__init__(self, node_identifier)
        self.number_of_points = number_of_points
        self.calibrate = calibrate

    def run(self):
        tx_id = self.client.cmd_mode(self.node_identifier, "maintenance")
        mode_response = self.wait_for_response(tx_id)
        print "Node has entered maintenance mode: ", mode_response
        tx_id = self.client.cmd_mode(self.node_identifier, "calibrate")
        mode_response = self.wait_for_response(tx_id)
        print "Node has entered calibrate mode: ", mode_response
        tx_id = int(time.time()*1000)
        cmd = {
            'request': 'calibrate',
            'tx_id': tx_id,
            'body': {
                'sensor': 'ph',
                'points': len(self.calibrate)
            }
        }
        self.client._send_to_node("Enter calibrate mode", self.node_identifier, cmd)
        ph_calibrate_response = self.wait_for_response(tx_id)
        print "Node has entered {body[points]}s point PH calibration mode: ".format(**cmd)
        count = 1
        for idx in range(len(self.calibrate)):
            slot, fluid_value, temp_compensation = calibrate_item = self.calibrate[idx]
            tx_id = int(time.time()*1000)
            cmd = {
                'request': 'calibrate',
                'tx_id': tx_id,
                'body': {
                    'sensor': 'ph',
                    'points': len(self.calibrate),
                    'phase': idx,
                    'slot': slot,
                    'fluid_value': fluid_value,
                    'temperature_compensation': temp_compensation
                }
            }
            self.client._send_to_node("Node has entered PH phase {slot}s".format(slot=slot), self.node_identifier, cmd)
            phase_response = self.wait_for_response(tx_id)
            phase_data_response = self.wait_for_response(tx_id)
            phase_data_response = self.wait_for_response(tx_id)
            phase_data_response = self.wait_for_response(tx_id)
            phase_data_response = self.wait_for_response(tx_id)
            phase_data_response = self.wait_for_response(tx_id)
            tx_id = int(time.time()*1000)
            cmd = {
                'request': 'calibrate',
                'tx_id': tx_id,
                'body': {
                    'sensor': 'ph',
                    'points': len(self.calibrate),
                    'phase': idx,
                    'slot': slot,
                    'command': 'accept'
                }
            }
            self.client._send_to_node("Send accept command for slot {slot}s".format(slot=slot), self.node_identifier, cmd)
            accept_response = self.wait_for_response(tx_id)
        calibration_complete_response = self.wait_for_response(tx_id)



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

    calibrate = subparsers.add_parser("calibrate", help="Simulate a calibration run")
    calibrate.add_argument('node_identifier')
    sensor = calibrate.add_subparsers(dest='sensor',  help="The Sensor type to calibrate: PH, DO, EC")

    EC = sensor.add_parser("EC",help="Calibrate a Electrical Conductivity Sensor (Salinity).")
    DO = sensor.add_parser("DO",help = "Calibrate a Disolved Oxygenn Sensor")


    PH = sensor.add_parser("PH", help="Calibrate a PH Sensor")
    ph_points = PH.add_subparsers(dest="points", help="The number of points of calibration to do")

    PH_1 = ph_points.add_parser("1", help="Do a 1 point PH calibration.")
    PH_1.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_1.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")

    PH_2 = ph_points.add_parser("2", help="Do a 2 point PH calibration.")
    PH_2_Second_Point = PH_2.add_subparsers(dest="second_point", help="Enter weather the second point will be high or low.")

    PH_2_HIGH = PH_2_Second_Point.add_parser("high", help="Enter weather the second point will be higher than 7.0")
    PH_2_HIGH.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_2_HIGH.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")
    PH_2_HIGH.add_argument("--high-ph", dest="high", default=10.0, type=float, help="The PH of the high calibration solution: 10.0")
    PH_2_HIGH.add_argument("--high-temp", dest="t_high", default=25.0, type=float, help="The temperature compensation for the high calibration point: 25.0")

    PH_2_LOW = PH_2_Second_Point.add_parser("low", help="Enter weather the second point will be lower than 7.0")
    PH_2_LOW.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_2_LOW.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")
    PH_2_LOW.add_argument("--low-ph", dest="low", default=4.0, type=float, help="The PH of the low calibration solution: 4.0")
    PH_2_LOW.add_argument("--low-temp", dest="t_low", default=25.0, type=float, help="The temperature compensation for the low calibration point: 25.0")


    PH_3 = ph_points.add_parser("3", help="Do a 3 point PH calibration.")
    PH_3.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_3.add_argument("--low-ph", dest="low", default=4.0, type=float, help="The PH of the low calibration solution: 4.0")
    PH_3.add_argument("--high-ph", dest="high", default=10.0, type=float, help="The PH of the high calibration solution: 10.0")

    PH_3.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")
    PH_3.add_argument("--high-temp", dest="t_high", default=25.0, type=float, help="The temperature compensation for the high calibration point: 25.0")
    PH_3.add_argument("--low-temp", dest="t_low", default=25.0, type=float, help="The temperature compensation for the low calibration point: 25.0")


    args = parser.parse_args()

    con = MqttClient(args.mqtt_host, args.P, (args.u, args.p))

    if args.action == 'listen':
        con.listen()
    elif args.action == 'ping':
        con.cmd_ping()
    elif args.action == 'mode':
        con.cmd_mode(args.node_identifier, args.mode)
    elif args.action == 'calibrate':
        if args.sensor == 'PH':
            if args.points == '1':
                con.ph_1_point_calibration(args.node_identifier, args.mid, args.t_mid)
            elif args.points == '2':
                if args.second_point == 'low':
                    con.ph_2_point_calibration(args.node_identifier, args.mid, args.t_mid, args.second_point, args.low, args.t_low)
                elif args.second_point == 'high':
                    con.ph_2_point_calibration(args.node_identifier, args.mid, args.t_mid, args.second_point, args.high, args.t_high)
            elif args.points == '3':
                con.ph_3_point_calibration(args.node_identifier, args.mid, args.t_mid, args.high, args.t_high, args.low, args.t_low)
        if args.sensor == 'EC':
            pass
        if args.sensor == 'DO':
            pass

    return 0

if __name__ == '__main__':
    sys.exit(main())
