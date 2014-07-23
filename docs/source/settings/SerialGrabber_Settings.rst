======================
SerialGrabber Settings
======================

Parameters located in the ``SerialGrabber_Settings.py`` file located in the configuration directory, see: :doc:`../CommandLine`.
 

.. _cache_collision_avoidance_delay:

cache_collision_avoidance_delay
-------------------------------
The minimum amount of time to let a transaction exist in the cache before being processed by the processor.

.. important:: This avoids the situation where the ``processor`` thread starts reading the cache entry before the ``reader`` has finished writing it.

.. code-block:: python

    cache_collision_avoidance_delay = 1
 
processor_sleep
---------------
The amount of time the processor should sleep between iterations.

.. code-block:: python

    processor_sleep = 1
    
watchdog_sleep
--------------
The amount of time that the watchdog thread will sleep for on each iteration.

.. code-block:: python

    watchdog_sleep = 1

reader_error_sleep
------------------
The amount of time the reader thread will sleep if there is an error. This avoids the reader's thread using all of the cpu when there is an error.

.. code-block:: python

    reader_error_sleep = 1  

startup_ignore_threshold_milliseconds
-------------------------------------
The amount of time that the reader will ignore input from the reader on startup. Some devices spew some garbage characters out on the serial port when they are powered up. 
This option helps avoid mistaking this garbage for real data.

.. code-block:: python

    startup_ignore_threshold_milliseconds = 1000

drop_carriage_return
--------------------
If this option is `True` then ``\r (0x0A)`` characters are removed from the data stream.

reader
------
An object that implements :class:`serial_grabber.reader.Reader`, see :doc:`../Reader`

.. code-block:: python

    reader = SerialReader('/dev/ttyUSB0', 115200,
        timeout=1,
        parity=serial.PARITY_NONE,
        stop_bits=1)

processor
---------
An object that implements :class:`serial_grabber.processor.Processor`, see: :doc:`../Processor`

.. code-block:: python

    from serial_grabber.processor.UploadProcessor import UploadProcessor

    processor = UploadProcessor("https://example.org/cgi-bin/data.py", form_params={'device':'Device-1'})

Example Config
--------------

.. literalinclude:: ../../../example_config/SerialGrabber_Settings.py