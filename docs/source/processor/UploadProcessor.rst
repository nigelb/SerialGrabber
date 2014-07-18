===============
UploadProcessor
===============

.. autoclass:: serial_grabber.processor.UploadProcessor.UploadProcessor

.. autoclass:: serial_grabber.processor.UploadProcessor.HTTPBasicAuthentication

.. code-block:: python

    from serial_grabber.processor.UploadProcessor import UploadProcessor, HTTPBasicAuthentication

    processor = UploadProcessor("https://example.org/cgi-bin/data.py",
        auth=HTTPBasicAuthentication("username", "password"),
        form_params={'device':'Device-1'}
    )



