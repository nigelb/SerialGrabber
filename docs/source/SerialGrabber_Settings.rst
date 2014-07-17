======================
SerialGrabber Settings
======================

uploader_collision_avoidance_delay - seconds
--------------------------------------------
The minimum amount of time to let a transaction exist in the cache before being processed by the processor.
 
uploader_sleep
--------------
This need to be refactored. It is used by the processor and the uploader.
The uploader should have it passed in the constructor, and the processor's should have a different name.

watchdog_sleep - seconds
------------------------
The amount of time that the watchdog thread will sleep for on each iteration.

reader_error_sleep
------------------
The amount of time the reader thread will sleep if there is an error. This avoids the reader's thread using all of the cpu when there is an error.  

startup_ignore_threshold_milliseconds
-------------------------------------
The amount of time that the reader will ignore input from the reader on startup. Some device spew some garbage out on the serial port when they are powered up. 
This option helps avoid mistaking this garbage for real data. 

drop_carriage_return
--------------------
If this option is `True` then \r (0x0A) characters are removed from the data stream.

reader
------
An object that implements [serial_grabber.reader.Reader](../serial_grabber/reader/__init__.py):

* [serial_grabber.reader.FileReader.FileReader](../serial_grabber/reader/FileReader.py)
* [serial_grabber.reader.SerialReader.SerialReader](../serial_grabber/reader/SerialReader.py)
* [serial_grabber.reader.TCP.TCPReader](../serial_grabber/reader/TCP.py)

processor
---------
An object that implements [serial_grabber.processor.Processor](../serial_grabber/processor/__init__.py):

* [serial_grabber.processor.ChunkingProcessor](Processors.md#ChunkingProcessor) [code](../serial_grabber/processor/__init__.py):
* [serial_grabber.processor.CompositeProcessor](../serial_grabber/processor/__init__.py):
* [serial_grabber.processor.TransformCompositeProcessor](../serial_grabber/processor/__init__.py):
* [serial_grabber.processor.CSVProcessors.CSVFileProcessor](../serial_grabber/processor/CSVProcessors.py)
* [serial_grabber.processor.FileAppenderProcessor.FileAppenderProcessor](../serial_grabber/processor/FileAppenderProcessor.py)
* [serial_grabber.processor.JsonFileProcessor.JsonFileProcessor](../serial_grabber/processor/JsonFileProcessor.py)
* [serial_grabber.processor.UploadProcessor.UploadProcessor](../serial_grabber/processor/UploadProcessor.py)

