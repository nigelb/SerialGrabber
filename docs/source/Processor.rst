=========
Processor
=========
.. toctree::
   :maxdepth: 2

   processor/ChunkingProcessor
   processor/CompositeProcessor
   processor/TransformProcessor
   processor/CSVFileProcessor
   processor/FileAppenderProcessor
   processor/JsonFileProcessor
   processor/UploadProcessor

Complex Examples
----------------
The following example are taken from some of our deployments.

Aquarium Example
++++++++++++++++

SerialGrabber_Settings.py
*************************
.. code-block:: python

    from serial_grabber.processor import CompositeProcessor, TransformProcessor, ChunkingProcessor
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
                ChunkingProcessor(PreviousMidnightBoundary(), 60 * 60 * 1000, "/home/user/data/aquarium/10_sec",CSVFileProcessor())),
    
            TransformProcessor(BlockAveragingTransform(10 * 60, averageAquariumData),
                ChunkingProcessor(PreviousMidnightBoundary(), 24 * 60 * 60 * 1000, "/home/user/data/aquarium/10_min",CSVFileProcessor())),
    
            TransformProcessor(BlockAveragingTransform(60 * 60, averageAquariumData),
                ChunkingProcessor(PreviousWeekStartBoundary(), 7 * 24 * 60 * 60 * 1000, "/home/user/data/aquarium/hour",CSVFileProcessor()))
        ])),
    
    
    ])

Eco Fest Example
++++++++++++++++

SerialGrabber_Settings.py
*************************
.. code-block:: python

    processor = CompositeProcessor([
        FileAppenderProcessor("/home/user/data/eco/all.txt"),
        TransformProcessor(EcoFestTransform(), CompositeProcessor([
            JsonFileProcessor("/home/user/data/eco/every_10.json", CountingTransactionFilter(10), 72),
            JsonFileProcessor("/home/user/data/eco/current.json", None, 1)]))
    ])