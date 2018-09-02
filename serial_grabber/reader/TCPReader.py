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
import select
import socket
import threading
import time

from serial_grabber.reader import Reader, MessageVerifier
from SerialGrabber_Storage import storage_cache as cache


class TCPReader(Reader):
    """
    Reads Digi Xbee/ZigBee API mode packets from the configured serial port, converts the packets into a stream for each MAC Address and passes the stream onto a :py:class:`serial.grabber.reader.TransactionExtractor`

    :param hostname: The hostname for the TCP connection to listen on
    :type hostname: basestring
    :param post: The TCP port to listen on
    :type port: int
    :param stream_transaction_factory: The function that creates a :py:class:`serial.grabber.reader.TransactionExtractor`
        with the specified stream_id
    :type stream_transaction_factory: fn(stream_id)
    :param message_verifier: Allow you to verify a transaction's output before it enters the cache.
    :type message_verifier: serial_grabber.reader.MessageVerifier
    :param binary: Weather the data received needs to be base64 encoded by the cache (otherwise binary data may mess up the cache json)
    :param bool escaped: The radio is in API mode 2
    """
    def __init__(self,
                 hostname,
                 port,
                 stream_transaction_factory,
                 message_verifier=MessageVerifier(),
                 client_filter=lambda a: True,
                 binary=True,
                 read_size=1024):
        Reader.__init__(self, None, 0)

        self.hostname = hostname
        self.port = port
        self.stream_transaction_factory = stream_transaction_factory
        self.message_verifier = message_verifier
        self.client_filter = client_filter
        self.binary = binary
        self.read_size = read_size

        self.connections = {}
        self.transactions = {}

        self.tcp_thread = None


    def tcp_listen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.settimeout(2)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.hostname, self.port))
        self.logger.info("Waiting for connection on %s:%d" %
                         (self.hostname, self.port))
        self.sock.listen(0)

        while self.isRunning.running:
            try:
                clientsocket, address = self.sock.accept()
                if not self.client_filter(address):
                    self.logger.error("Client: %s:%s filteres by client_filter."%address)
                    continue
                client_id = "%s:%s"%address
                self.logger.info("Connection from %s" % client_id)
                clientsocket.setblocking(False)
                if client_id in self.connections:
                    self.logger.warn("Client: %s already exists. Closing existing connection."%client_id)
                    con = self.connections[client_id]
                    con.shutdown(2)
                    con.close()
                self.connections[client_id] = clientsocket

                tf = self.stream_transaction_factory(client_id)
                self.transactions[clientsocket] = tf
                tf.set_callback(lambda stream_id, transaction: self.handle_transaction(stream_id, transaction))


            except Exception, e:
                self.logger.exception("Error in TCP Server")

    def handle_transaction(self, stream_id, transaction):
        try:
            isValid, response = self.message_verifier.verify_message(transaction)
            entry = cache.make_payload(transaction, binary=self.binary)
            entry['stream_id'] = stream_id
            path = cache.cache(entry)

            if isValid:
                self.counter.read()
                self.counter.update()
            else:
                storage_archive.archive(path, name="invalid")
                self.counter.invalid()
                self.counter.update()

        except Exception, e:
            self.logger.exception("Error handling transaction from: %s %%s" % stream_id, e)

    def setup(self):
        def curry():
            self.tcp_listen()

        self.tcp_thread = threading.Thread(target=curry)
        self.tcp_thread.setDaemon(True)
        self.tcp_thread.setName("TCPServer Listener")
        self.tcp_thread.start()

    def close(self):
        for con_id in self.connections:
            try:
                con = self.connections[con_id]
                con.shutdown(2)
                con.close()
            except Exception as e:
                self.logger.exception("Error closing connection: %s"%con_id)

    def read_data(self):
        connections = self.connections.values()
        ready_to_read, ready_to_write, in_error = \
            select.select(connections, connections, connections, 5)
        count = 0
        for id, con in self.connections.items():
            if con in ready_to_read:
                try:
                    c = con.recv(self.read_size)
                    if len(c) == 0:
                        self.logger.info("Client %s closed."%id)
                        try:
                            con.shutdown(2)
                            con.close()
                        except:
                            pass
                        del self.connections[id]
                        del self.transactions[con]
                    else:
                        self.transactions[con].write(c)
                        count += len(c)
                except socket.error, r:
                    self.logger.info("Client %s closed: %s."%(id, r))
                    del self.connections[id]
                    del self.transactions[con]

        return count

    def run(self):
        while self.isRunning.running:
            try:
                if self.tcp_thread is None:
                    self.setup()
                rec_count = self.read_data()
                if rec_count == 0:
                    time.sleep(0.1)
            except Exception, w:
                self.logger.exception("ERROR!")




