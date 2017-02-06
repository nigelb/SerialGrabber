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
        tx_id = self.get_next_tx_id()
        self._send_to_node("Send mode change to %s" % node_identifier,
                           node_identifier, self.build_mode_request(mode, tx_id))
        return tx_id

    def cmd_request(self, node_identifier, request):
        """
        Issues the request to a node
        """
        self._send_to_node("Send request to %s" % node_identifier,
                           node_identifier, request)

    def get_next_tx_id(self):
        """
        Gets a new transaction id
        """
        return int(time.time()*1000)

    def build_mode_request(self, mode, tx_id):
        """
        Builds a mode request string
        """
        request = {'request': 'mode', 'mode': mode, 'tx_id': tx_id}
        return request

    def send_request_and_await_response(self, node_identifier, request, tx_id):
        """
        Sends the passed in request to the node and waits for a response with a matching traansaction id
        :param node_identifier:
        :param request:
        :param tx_id:
        :return:
        """
        self.single = False
        request = Request(node_identifier, request, tx_id)
        request_thread = threading.Thread(
            target=request,
            args=(self._stopping, self),
            name="Request")
        request_thread.daemon = True
        request_thread.start()
        self._con.on_message = request.on_message
        self.listen()

    def ph_3_point_calibration(self, node_identifier, mid, t_mid, high, t_high, low, t_low):
        calibrate = [
            ["mid", mid, t_mid],
            ["high", high, t_high],
            ["low", low, t_low],
        ]
        return self.run_ph_calibration(node_identifier, 3, calibrate)

    ### PH Calibrations

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
            target=ph_cal,
            args=(self._stopping, self),
            name="PH Calibration")
        calibration_thread.daemon = True
        calibration_thread.start()
        self._con.on_message = ph_cal.on_message
        self.listen()

    ### EC Calibrations

    def ec_2_point_calibration(self, node_identifier, k_value, t_dry, high, t_high, low, t_low):
        calibrate = [
            ["dry", None, t_dry],
            ["high", high, t_high],
            ["low", low, t_low]
        ]
        return self.run_ec_calibration(node_identifier, 2, k_value, calibrate)

    def ec_1_point_calibration(self, node_identifier, k_value, t_dry, single, t_single):
        calibrate = [
            ["dry", None, t_dry],
            ["single", single, t_single]
        ]
        return self.run_ec_calibration(node_identifier, 1, k_value, calibrate)

    def run_ec_calibration(self, node_identifier, number_of_points, k_value, calibrate):
        self.single = False
        ec_cal = EC_Calibration(node_identifier, number_of_points, k_value, calibrate)
        calibration_thread = threading.Thread(
            target=ec_cal,
            args=(self._stopping, self),
            name="EC Calibration")
        calibration_thread.daemon = True
        calibration_thread.start()
        self._con.on_message = ec_cal.on_message
        self.listen()

    ### DO Calibrations

    def do_2_point_calibration(self, node_identifier, t_air, p_air, s_air, t_zero, p_zero, s_zero):
        calibrate = [
            ["air", t_air, p_air, s_air],
            ["zero_do", t_zero, p_zero, s_zero]
        ]
        return self.run_do_calibration(node_identifier, 2, calibrate)

    def do_1_point_calibration(self, node_identifier, t_air, p_air, s_air):
        calibrate = [
            ["air", t_air, p_air, s_air]
        ]
        return self.run_do_calibration(node_identifier, 1, calibrate)

    def run_do_calibration(self, node_identifier, number_of_points, calibrate):
        self.single = False
        do_cal = DO_Calibration(node_identifier, number_of_points, calibrate)
        calibration_thread = threading.Thread(
            target=do_cal,
            args=(self._stopping, self),
            name="DO Calibration")
        calibration_thread.daemon = True
        calibration_thread.start()
        self._con.on_message = do_cal.on_message
        self.listen()

    ### TU Calibrations

    def tu_2_point_calibration(self, node_identifier, t_low, ntu_low, t_high, ntu_high):
        calibrate = [
            ["low", t_low, ntu_low],
            ["high", t_high, ntu_high]
        ]
        return self.run_tu_calibration(node_identifier, 2, calibrate)

    def run_tu_calibration(self, node_identifier, number_of_points, calibrate):
        self.single = False
        tu_cal = TU_Calibration(node_identifier, number_of_points, calibrate)
        calibration_thread = threading.Thread(
            target=tu_cal,
            args=(self._stopping, self),
            name="TU Calibration")
        calibration_thread.daemon = True
        calibration_thread.start()
        self._con.on_message = tu_cal.on_message
        self.listen()


class Request:
    def __init__(self, node_identifier, request, tx_id):
        self.node_identifier = node_identifier
        self.message_lock = threading.Lock()
        self.messages = {}
        self.request = request
        self.tx_id = tx_id

    def __call__(self, *args, **kwargs):
        self._stopping, self.client = args
        time.sleep(1)
        print "Starting Request Thread"
        self.run()
        print "Request complete"
        self._stopping.set()

    def wait_for_response(self, tx_id):
        found = False
        result = None
        if tx_id == '':
            wait_tx_id = 0
        else:
            wait_tx_id = tx_id
        while not found:
            self.message_lock.acquire()
            if wait_tx_id in self.messages:
                result = self.messages[wait_tx_id]
                del self.messages[wait_tx_id]
                found = True
            if 0 in self.messages:
                result = self.messages[0]
                del self.messages[0]
                print "Node has timed out"
                found = True
            self.message_lock.release()
            time.sleep(0.01)
        return result

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload)
        if payload["nodeIdentifier"] == self.node_identifier:
            if 'notify' in payload:
                print "Node is pinging from Live mode. Your request has probably been ignored."
            if 'response' in payload:
                self.message_lock.acquire()
                if 'tx_id' in payload:
                    if payload['tx_id'] == '':
                        tx_id = 0
                    else:
                        tx_id = int(payload['tx_id'])
                else:
                    tx_id = 0
                self.messages[tx_id] = payload
                self.message_lock.release()

    def run(self):
        self.client.cmd_request(self.node_identifier, self.request)
        print "Waiting for response with tx_id:", self.tx_id, "..."
        response = self.wait_for_response(self.tx_id)
        print "Node responded with: ", response


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
        if tx_id == '':
            wait_tx_id = 0
        else:
            wait_tx_id = tx_id
        while not found:
            self.message_lock.acquire()
            if wait_tx_id in self.messages:
                result = self.messages[wait_tx_id]
                del self.messages[wait_tx_id]
                found = True
            self.message_lock.release()
            time.sleep(0.01)
        return result

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload)
        if payload["nodeIdentifier"] == self.node_identifier:
            if 'tx_id' in payload and 'response' in payload:
                self.message_lock.acquire()
                if payload['tx_id'] == '':
                    tx_id = 0
                else:
                    tx_id = int(payload['tx_id'])
                self.messages[tx_id] = payload
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
        print "Node has entered {body[points]} point PH calibration mode: ".format(**cmd)
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
            self.client._send_to_node("Node has entered PH phase {slot}".format(slot=slot), self.node_identifier, cmd)
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
            self.client._send_to_node("Send accept command for slot {slot}".format(slot=slot), self.node_identifier, cmd)
            accept_response = self.wait_for_response(tx_id)
        tx_id = ''
        calibration_complete_response = self.wait_for_response(tx_id)


class EC_Calibration(Calibration):
    def __init__(self, node_identifier, number_of_points, k_value, calibrate):
        Calibration.__init__(self, node_identifier)
        self.number_of_points = number_of_points
        self.k_value = k_value
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
                'sensor': 'ec',
                'points': self.number_of_points,
                'k-value': self.k_value
            }
        }
        self.client._send_to_node("Enter calibrate mode", self.node_identifier, cmd)
        ph_calibrate_response = self.wait_for_response(tx_id)
        print "Node has entered {body[points]} point EC calibration mode: ".format(**cmd)
        count = 1
        for idx in range(len(self.calibrate)):
            slot, fluid_value, temp_compensation = calibrate_item = self.calibrate[idx]
            tx_id = int(time.time()*1000)
            cmd = {
                'request': 'calibrate',
                'tx_id': tx_id,
                'body': {
                    'sensor': 'ec',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'temperature_compensation': temp_compensation
                }
            }
            if fluid_value is not None:
                cmd['body']['fluid_value'] = fluid_value

            self.client._send_to_node("Node has entered EC phase {slot}".format(slot=slot), self.node_identifier, cmd)
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
                    'sensor': 'ec',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'command': 'accept'
                }
            }
            self.client._send_to_node("Send accept command for slot {slot}".format(slot=slot), self.node_identifier, cmd)
            accept_response = self.wait_for_response(tx_id)
        tx_id = ''
        calibration_complete_response = self.wait_for_response(tx_id)

class DO_Calibration(Calibration):
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
                'sensor': 'do',
                'points': self.number_of_points
            }
        }
        self.client._send_to_node("Enter calibrate mode", self.node_identifier, cmd)
        ph_calibrate_response = self.wait_for_response(tx_id)
        print "Node has entered {body[points]} point DO calibration mode: ".format(**cmd)
        count = 1
        for idx in range(len(self.calibrate)):
            slot, temp_compensation, pressure, salinity = calibrate_item = self.calibrate[idx]
            tx_id = int(time.time()*1000)
            cmd = {
                'request': 'calibrate',
                'tx_id': tx_id,
                'body': {
                    'sensor': 'do',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'temperature_compensation': temp_compensation,
                    'pressure': pressure,
                    'salinity': salinity
                }
            }

            self.client._send_to_node("Node has entered DO phase {slot}".format(slot=slot), self.node_identifier, cmd)
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
                    'sensor': 'do',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'command': 'accept'
                }
            }
            self.client._send_to_node("Send accept command for slot {slot}".format(slot=slot), self.node_identifier, cmd)
            accept_response = self.wait_for_response(tx_id)
        tx_id = ''
        calibration_complete_response = self.wait_for_response(tx_id)

class TU_Calibration(Calibration):
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
                'sensor': 'tu',
                'points': self.number_of_points
            }
        }
        self.client._send_to_node("Enter calibrate mode", self.node_identifier, cmd)
        ph_calibrate_response = self.wait_for_response(tx_id)
        print "Node has entered {body[points]} point TU calibration mode: ".format(**cmd)
        count = 1
        for idx in range(len(self.calibrate)):
            slot, temp_compensation, turbidity = calibrate_item = self.calibrate[idx]
            tx_id = int(time.time()*1000)
            cmd = {
                'request': 'calibrate',
                'tx_id': tx_id,
                'body': {
                    'sensor': 'tu',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'temperature_compensation': temp_compensation,
                    'turbidity': turbidity
                }
            }

            self.client._send_to_node("Node has entered TU phase {slot}".format(slot=slot), self.node_identifier, cmd)
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
                    'sensor': 'tu',
                    'points': self.number_of_points,
                    'phase': idx,
                    'slot': slot,
                    'command': 'accept'
                }
            }
            self.client._send_to_node("Send accept command for slot {slot}".format(slot=slot), self.node_identifier, cmd)
            accept_response = self.wait_for_response(tx_id)
        tx_id = ''
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
    sensor = calibrate.add_subparsers(dest='sensor',  help="The Sensor type to calibrate: PH, DO, EC, TU")

    PH = sensor.add_parser("PH", help="Calibrate a PH Sensor")
    ph_points = PH.add_subparsers(dest="points", help="The number of points of calibration to do")

    PH_1 = ph_points.add_parser("1", help="Do a 1 point PH calibration.")
    PH_1.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_1.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")

    PH_2 = ph_points.add_parser("2", help="Do a 2 point PH calibration.")
    PH_2_Second_Point = PH_2.add_subparsers(dest="second_point", help="Enter whether the second point will be high or low.")

    PH_2_HIGH = PH_2_Second_Point.add_parser("high", help="Enter whether the second point will be higher than 7.0")
    PH_2_HIGH.add_argument("--mid-ph", dest="mid", default=7.0, type=float, help="The PH of the middle calibration solution: 7.0")
    PH_2_HIGH.add_argument("--mid-temp", dest="t_mid", default=25.0, type=float, help="The temperature compensation for the middle calibration point: 25.0")
    PH_2_HIGH.add_argument("--high-ph", dest="high", default=10.0, type=float, help="The PH of the high calibration solution: 10.0")
    PH_2_HIGH.add_argument("--high-temp", dest="t_high", default=25.0, type=float, help="The temperature compensation for the high calibration point: 25.0")

    PH_2_LOW = PH_2_Second_Point.add_parser("low", help="Enter whether the second point will be lower than 7.0")
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


    EC = sensor.add_parser("EC", help="Calibrate a Electrical Conductivity Sensor (Salinity)")
    EC.add_argument("--k-value", dest="k_value", default=1.0, type=float, help="The probe k-value which could be 0.1, 1 or 10: 1.0")
    ec_points = EC.add_subparsers(dest="points", help="The number of points of calibration to do")

    EC_1 = ec_points.add_parser("1", help="Do a 1 point EC calibration.")
    EC_1.add_argument("--dry-temp", dest="t_dry", default=25.0, type=float, help="The temperature compensation for the dry calibration point: 25.0")
    EC_1.add_argument("--single-ec", dest="single", default=10.0, type=float, help="The EC of the single calibration solution: 10.0")
    EC_1.add_argument("--single-temp", dest="t_single", default=25.0, type=float, help="The temperature compensation for the single calibration point: 25.0")

    EC_2 = ec_points.add_parser("2", help="Do a 2 point EC calibration.")
    EC_2.add_argument("--dry-temp", dest="t_dry", default=25.0, type=float, help="The temperature compensation for the dry calibration point: 25.0")
    EC_2.add_argument("--low-ec", dest="low", default=4.0, type=float, help="The EC of the low calibration solution: 4.0")
    EC_2.add_argument("--low-temp", dest="t_low", default=25.0, type=float, help="The temperature compensation for the low calibration point: 25.0")
    EC_2.add_argument("--high-ec", dest="high", default=10.0, type=float, help="The EC of the high calibration solution: 10.0")
    EC_2.add_argument("--high-temp", dest="t_high", default=25.0, type=float, help="The temperature compensation for the high calibration point: 25.0")

    DO = sensor.add_parser("DO", help="Calibrate a Disolved Oxygen Sensor")
    do_points = DO.add_subparsers(dest="points", help="The number of points of calibration to do")

    DO_1 = do_points.add_parser("1", help="Do a 1 point DO calibration.")
    DO_1.add_argument("--air-temp", dest="t_air", default=25.0, type=float, help="The temperature compensation for the air-based DO calibration point: 25.0")
    DO_1.add_argument("--air-pressure", dest="p_air", default=101.32, type=float, help="The pressure compensation for the air-based DO calibration point: 101.32")
    DO_1.add_argument("--air-salinity", dest="s_air", default=0.0, type=float, help="The salinity compensation for the air-based DO calibration point: 0.0")

    DO_2 = do_points.add_parser("2", help="Do a 2 point DO calibration.")
    DO_2.add_argument("--air-temp", dest="t_air", default=25.0, type=float, help="The temperature compensation for the air-based DO calibration point: 25.0")
    DO_2.add_argument("--air-pressure", dest="p_air", default=101.32, type=float, help="The pressure compensation for the air-based DO calibration point: 101.32")
    DO_2.add_argument("--air-salinity", dest="s_air", default=0.0, type=float, help="The salinity compensation for the air-based DO calibration point: 0.0")
    DO_2.add_argument("--zero-temp", dest="t_zero", default=25.0, type=float, help="The temperature compensation for the zero-based DO calibration point: 25.0")
    DO_2.add_argument("--zero-pressure", dest="p_zero", default=101.32, type=float, help="The pressure compensation for the zero-based DO calibration point: 101.32")
    DO_2.add_argument("--zero-salinity", dest="s_zero", default=0.0, type=float, help="The salinity compensation for the zero-based DO calibration point: 0.0")

    TU = sensor.add_parser("TU", help="Calibrate a Turbidity Sensor")
    tu_points = TU.add_subparsers(dest="points", help="The number of points of calibration to do")

    TU_2 = tu_points.add_parser("2", help="Do a 2 point TU (Turbidity) calibration.")
    TU_2.add_argument("--low-temp", dest="t_low", default=25.0, type=float, help="The temperature compensation for the low calibration point: 25.0")
    TU_2.add_argument("--low-ntu", dest="ntu_low", default=120.0, type=float, help="The turbidity of the low calibration solution: 120.0")
    TU_2.add_argument("--high-temp", dest="t_high", default=25.0, type=float, help="The temperature compensation for the high calibration point: 25.0")
    TU_2.add_argument("--high-ntu", dest="ntu_high", default=120.0, type=float, help="The turbidity of the high calibration solution: 1800.0")


    args = parser.parse_args()

    con = MqttClient(args.mqtt_host, args.P, (args.u, args.p))

    if args.action == 'listen':
        con.listen()
    elif args.action == 'ping':
        con.cmd_ping()
    elif args.action == 'mode':
        tx_id = con.get_next_tx_id()
        request = con.build_mode_request(args.mode, tx_id)
        con.send_request_and_await_response(args.node_identifier, request, tx_id)
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
            if args.points == '1':
                con.ec_1_point_calibration(args.node_identifier, args.k_value, args.t_dry, args.single, args.t_single)
            elif args.points == '2':
                con.ec_2_point_calibration(args.node_identifier, args.k_value, args.t_dry, args.high, args.t_high, args.low, args.t_low)
        if args.sensor == 'DO':
            if args.points == '1':
                con.do_1_point_calibration(args.node_identifier, args.t_air, args.p_air, args.s_air)
            elif args.points == '2':
                con.do_2_point_calibration(args.node_identifier, args.t_air, args.p_air, args.s_air, args.t_zero, args.p_zero, args.s_zero)
        if args.sensor == 'TU':
            if args.points == '2':
                con.tu_2_point_calibration(args.node_identifier, args.t_low, args.ntu_low, args.t_high, args.ntu_high)

    return 0

if __name__ == '__main__':
    sys.exit(main())
