=========
Processor
=========


CompositeProcessor
------------------

.. autoclass:: serial_grabber.processor.CompositeProcessor


CSVFileProcessor
----------------

.. autoclass:: serial_grabber.processor.CSVProcessors.CSVFileProcessor


FileAppenderProcessor
---------------------

.. autoclass:: serial_grabber.processor.FileAppenderProcessor.FileAppenderProcessor


JsonFileProcessor
-----------------

.. autoclass:: serial_grabber.processor.JsonFileProcessor.JsonFileProcessor


RollingFilenameProcessor
------------------------

.. autoclass:: serial_grabber.processor.RollingFilenameProcessor

.. code-block:: python

    from serial_grabber.processor import RollingFilenameProcessor

    processor = RollingFilenameProcessor(
        PreviousMidnightBoundary(), 60 * 60 * 1000,
        "/home/user/data/aquarium/10_sec",
        "csv",
        CSVFileProcessor()
    )

TransformProcessor
------------------

.. autoclass:: serial_grabber.processor.TransformProcessor

UploadProcessor
---------------

.. autoclass:: serial_grabber.processor.UploadProcessor.UploadProcessor

.. autoclass:: serial_grabber.processor.UploadProcessor.HTTPBasicAuthentication

.. code-block:: python

    from serial_grabber.processor.UploadProcessor import UploadProcessor, HTTPBasicAuthentication

    processor = UploadProcessor("https://example.org/cgi-bin/data.py",
        auth=HTTPBasicAuthentication("username", "password"),
        form_params={'device':'Device-1'}
    )





