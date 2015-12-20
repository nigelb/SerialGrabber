=======
Archive
=======
Once a payload has been successfully processed by the configure processor the payload item is removed from the cache and
sent to the configured archive.

The Archive settings can be set in: :doc:`settings/SerialGrabber_Storage`.


FileSystemArchive
-----------------
.. autoclass:: serial_grabber.archive.FileSystemArchive

DumpArchive
-----------
.. autoclass:: serial_grabber.archive.DumpArchive

JSONLineArchive
---------------
.. autoclass:: serial_grabber.archive.JSONLineArchive
