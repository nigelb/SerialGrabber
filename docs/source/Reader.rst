=======
Readers
=======

FileReader
----------
.. autoclass:: serial_grabber.reader.FileReader.FileReader

.. code-block:: python

    from serial_grabber.reader.FileReader import FileReader

    ...

    reader = FileReader("data.txt")

SerialReader
------------
.. autoclass:: serial_grabber.reader.SerialReader.SerialReader

.. code-block:: python

    from serial_grabber.reader.SerialReader import SerialReader

    ...

    reader = SerialReader('/dev/ttyUSB0', 115200,
        timeout=1,
        parity=serial.PARITY_NONE,
        stop_bits=1)


TCPReader
---------
.. autoclass:: serial_grabber.reader.TCP.TCPReader

.. code-block:: python

    from serial_grabber.reader.TCP import TCPReader

    ...

    reader = TCPReader("example.org", 8111)


DigiRadioReader
---------------
.. autoclass:: serial_grabber.reader.Xbee.DigiRadioReader

.. code-block:: python

    import serial
    from serial_grabber.reader.Xbee import DigiRadioReader

    ...

    reader = DigiRadioReader("/dev/ttyUSB0", 115200,
                             timeout=60,
                             parity=serial.PARITY_NONE,
                             stop_bits=serial.STOPBITS_ONE,
                             packet_filter=lambda packet: packet['id'] == 'rx',
                             escaped=True)