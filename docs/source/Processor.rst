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

HTTP Basic Authentication:

.. code-block:: python

    from serial_grabber.processor.UploadProcessor import UploadProcessor
    from requests.auth import HTTPBasicAuth

    processor = UploadProcessor("https://example.org/cgi-bin/data.py",
        auth=HTTPBasicAuth("username", "password"),
        form_params={'device':'Device-1'}
    )


HTTP Digest Authentication with SSL verification disabled:

.. code-block:: python

    from serial_grabber.processor.UploadProcessor import UploadProcessor
    from requests.auth import HTTPDigestAuth

    processor = UploadProcessor("https://example.org/cgi-bin/data.py",
        auth=HTTPDigestAuth("username", "password"),
        form_params={'device':'Device-1'},
        request_kw={'verify':False}    
    )




