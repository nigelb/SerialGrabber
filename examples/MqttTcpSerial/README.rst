Overview
========

This example is for the following setup::

        MQTT <-> SerialGrabber <-TCP-> fake_buoy

This is meant to enabled debugging and development of systems that interact with SerialGrabber attached Sensor-Q buoys  via MQTT.

Getting Started
===============

You need to have an existing MQTT broker, such as `mosquitto<http://mosquitto.org>`_ or ActiveMQ. The following examples assume ActiveMQ using username/password auth of system/manager.

MQTT listener
-------------

Setup a listener on the MQTT topics so you can observe the traffic. If you have paho-mqtt installed the following commands can be used.

Data traffic::


        stomp -H localhost -P 61613 -U system -W manager -L /topic/data


Maintenance responses::


        stomp -H localhost -P 61613 -U system -W manager -L /topic/maintenance


SerialGrabber
-------------

Start SerialGrabber using the ``examples/MqttTcpSerial`` configuration. This will connect to the MQTT bus, and will expect the fake buoy will connect via TCP on port ``8099``::

        serial_grabber --config-dir examples/MqttTcpSerial


Fake buoy
---------

The fake buoy is also started from within the SerialGrabber virtualenv, pointing to the listening *SerialGrabber* instance, and specifying the ``serial`` protocol (as opposed to Xbee)::

        fake_buoy tcp localhost 8099 serial


Sending Commands
================

You can send commands to the fake buoy using hand crafted MQTT payloads directed to the buoy's topic.
