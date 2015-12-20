=======
Readers
=======

FileReader
----------
.. autoclass:: serial_grabber.reader.FileReader.FileReader

.. code-block:: python

    from serial_grabber.reader.FileReader import FileReader

    ...

    transaction = TransactionExtractor("default", "BEGIN DATA", "END DATA")
    reader = FileReader(transaction, "data.txt")

SerialReader
------------
.. autoclass:: serial_grabber.reader.SerialReader.SerialReader

.. code-block:: python

    from serial_grabber.reader.SerialReader import SerialReader

    ...

    transaction = TransactionExtractor("default", "BEGIN DATA", "END DATA")
    reader = SerialReader(transaction,
                          '/dev/ttyUSB0',
                          115200,
                          timeout=1,
                          parity=serial.PARITY_NONE,
                          stop_bits=1)


TCPReader
---------
.. autoclass:: serial_grabber.reader.TCP.TCPReader

.. code-block:: python

    from serial_grabber.reader.TCP import TCPReader

    ...

    transaction = TransactionExtractor("default", "BEGIN DATA", "END DATA")
    reader = TCPReader(transaction, "example.org", 8111)


PacketRadioReader
-----------------
.. autoclass:: serial_grabber.reader.Xbee.PacketRadioReader

.. code-block:: python

    import serial
    from serial_grabber.reader.Xbee import PacketRadioReader

    ...

    reader = DigiRadioReader("/dev/ttyUSB0", 115200,
                             timeout=60,
                             parity=serial.PARITY_NONE,
                             stop_bits=serial.STOPBITS_ONE,
                             packet_filter=lambda packet: packet['id'] == 'rx',
                             escaped=True)


StreamRadioReader
-----------------
.. autoclass:: serial_grabber.reader.Xbee.StreamRadioReader

.. code-block:: python

    import serial
    from serial_grabber.reader.Xbee import StreamRadioReader

    def create_stream(stream_id):
        print " ".join([format(ord(x), "02x") for x in stream_id])
        return TransactionExtractor(stream_id, start_del, end_del)

    reader = DigiRadioReader(create_stream,
                             "/dev/ttyUSB0",
                             115200,
                             timeout=60,
                             parity=serial.PARITY_NONE,
                             stop_bits=serial.STOPBITS_ONE,
                             packet_filter=lambda packet: packet['id'] == 'rx',
                             escaped=True)

====================
TransactionExtractor
====================
.. autoclass:: serial_grabber.reader.TransactionExtractor