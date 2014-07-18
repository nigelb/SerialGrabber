===================
SerialGrabber Paths
===================

Parameters located in the ``SerialGrabber_Paths.py`` file located in the configuration directory, see: :doc:`../CommandLine`.

.. _cache_dir:

cache_dir
---------
The location of the cache directory, see :doc:`../DataLifeCycle`

.. code-block:: python

    cache_dir = os.path.join(data_logger_dir, "cache")

archive_dir
-----------
The location of the archive directory, see :doc:`../DataLifeCycle`

.. code-block:: python

    archive_dir = os.path.join(data_logger_dir, "archive")

Example Config
--------------

.. literalinclude:: ../../../example_config/SerialGrabber_Paths.py