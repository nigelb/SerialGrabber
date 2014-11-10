================
Aquarium Example
================

An Arduino mega is being used to control the PH of an aquarium by injecting CO\ :sub:`2` into the water.
The Arduino outputs data on its serial port so that it can be captured and displayed in real time.



Sample Data
-----------

.. code-block:: text

    BEGIN AQUARIUM
    temp,25.06,20.00
    ph,3.49,7.00
    temp_pid,1.0000000000,-0.3000000000,-1.0000000000,255.0000000000
    ph_pid,1.0000000000,1.0000000000,1.0000000000,736.9911499023
    END AQUARIUM
    BEGIN AQUARIUM
    temp,25.06,20.00
    ph,3.49,7.00
    temp_pid,1.0000000000,-0.3000000000,-1.0000000000,255.0000000000
    ph_pid,1.0000000000,1.0000000000,1.0000000000,744.0111694335
    END AQUARIUM


Configuration
-------------

SerialGrabber_Settings.py
+++++++++++++++++++++++++

.. code-block:: python

    import serial
    from serial_grabber.reader import TransactionExtractor
    from serial_grabber.reader.FileReader import FileReader
    from serial_grabber.reader.SerialReader import SerialReader
    from serial_grabber.processor.UploadProcessor import UploadProcessor

    #Serial Settings
    timeout = 1
    port = "/dev/ttyUSB0"
    baud = 115200
    parity = serial.PARITY_NONE
    stop_bits = 1

    #Settings
    cache_collision_avoidance_delay = 1
    processor_sleep = 1
    watchdog_sleep = 1

    reader_error_sleep = 1

    drop_carriage_return = True

    transaction = TransactionExtractor("default", "BEGIN AQUARIUM", "END AQUARIUM")

    reader = SerialReader(transaction,
                          1000,
                          port,
                          baud,
                          timeout=timeout,
                          parity=parity,
                          stop_bits=stop_bits)

    processor = CompositeProcessor([
        FileAppenderProcessor("all.txt"),
        TransformProcessor(AquariumTransform(), CompositeProcessor([
            JsonFileProcessor("data/processed/current.json", None, 1),
            TransformProcessor(BlockAveragingTransform(10, averageAquariumData),
                RollingFilenameProcessor(PreviousMidnightBoundary(), 60 * 60 * 1000, "/home/user/data/aquarium/10_sec","csv",CSVFileProcessor())),

            TransformProcessor(BlockAveragingTransform(10 * 60, averageAquariumData),
                RollingFilenameProcessor(PreviousMidnightBoundary(), 24 * 60 * 60 * 1000, "/home/user/data/aquarium/10_min","csv",CSVFileProcessor())),

            TransformProcessor(BlockAveragingTransform(60 * 60, averageAquariumData),
                RollingFilenameProcessor(PreviousWeekStartBoundary(), 7 * 24 * 60 * 60 * 1000, "/home/user/data/aquarium/hour","csv",CSVFileProcessor()))
        ])),


    ])


