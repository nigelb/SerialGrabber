===============
Data Life Cycle
===============

There are two threads, the Reader thread and the Processor thread.

Reader Thread
-------------
The Reader

#. Reads the data from the configured source, see :ref:`reader` and :doc:`Reader`.
#. Writes the data into the cache directory, see: :ref:`cache_dir`, and :doc:`Cache`

Processor Thread
----------------
The Processor

#. Waits until a cache entry is older than :ref:`cache_collision_avoidance_delay`.
#. Processes the data with the configured processor, see :doc:`Processor`.
    #. if the processing was successful the cache entry in moved into the archive, see :ref:`archive_dir` and :doc:`Archive`.
    #. otherwise it is left in the cache and it will be reprocessed in a later cycle.