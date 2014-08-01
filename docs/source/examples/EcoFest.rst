Eco Fest Example
----------------

Configuration
-------------

SerialGrabber_Settings.py
+++++++++++++++++++++++++

.. code-block:: python

    processor = CompositeProcessor([
        FileAppenderProcessor("/home/user/data/eco/all.txt"),
        TransformProcessor(EcoFestTransform(), CompositeProcessor([
            JsonFileProcessor("/home/user/data/eco/every_10.json", CountingTransactionFilter(10), 72),
            JsonFileProcessor("/home/user/data/eco/current.json", None, 1)]))
    ])