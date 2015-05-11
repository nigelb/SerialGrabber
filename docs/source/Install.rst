========================
Installing SerialGrabber
========================

Dependencies
------------
SerialGrabber depends on these packages:

* `pyserial`_
* `requests`_

and optionally:

* `xbee`_

The easiest way to install these packages is to use pip:

.. code-block:: bash

    ~ $ pip install pyserial requests
    .
    .
    .

and optionally:

.. code-block:: bash

    ~ $ pip install xbee
    .
    .
    .

From Source
-----------

To install Serial Grabber run the following commands as ``root``:

.. code-block:: bash

    ~ $ git clone https://github.com/nigelb/SerialGrabber.git
    ~ $ cd SerialGrabber
    ~/SerialGrabber $ python setup.py install

After this you need to create your configuration directory. The easiest way to do this is to copy the ``example_config``
directory, for example if you wanted to use ``/etc/SerialGrabber`` as your configuration directory:

.. code-block:: bash

    ~/SerialGrabber $ cp -R SerialGrabber/example_config /etc/SerialGrabber

Then edit the configuration files and change them according to your needs.

.. _pyserial: https://pypi.python.org/pypi/pyserial
.. _requests: https://pypi.python.org/pypi/requests
.. _xbee: https://pypi.python.org/pypi/xbee
