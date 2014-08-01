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

    from serial_grabber.processor import CompositeProcessor, TransformProcessor, RollingFilenameProcessor
    from serial_grabber.processor.CSVProcessors import CSVFileProcessor
    from serial_grabber.processor.JsonFileProcessor import JsonFileProcessor
    from serial_grabber.transform import BlockAveragingTransform
    from serial_grabber.transform.AquariumTransform import AquariumTransform, averageAquariumData
    from serial_grabber.util import PreviousMidnightBoundary, PreviousWeekStartBoundary

    ...

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

SerialGrabber_State.py
++++++++++++++++++++++

.. code-block:: python

    from serial_grabber.state import matches, begin_transaction, end_transaction
    try:
        from collections import OrderedDict
    except:
        from ordereddict import OrderedDict

    def reader_state():
        READER_STATE = OrderedDict()
        READER_STATE[matches("BEGIN AQUARIUM")] = begin_transaction(READER_STATE)
        READER_STATE[matches("END AQUARIUM")] = end_transaction(READER_STATE)
        return READER_STATE

