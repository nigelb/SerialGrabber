=====================
Running SerialGrabber
=====================
Once you have installed SerialGravver and created your configuration you can launch SerialGrabber from the command line:

.. code-block:: bash

	#~> serial_grabber --help
	usage: serial_grabber [-h] [--config-dir <config_dir>]

	Serial Grabber will read the configured serial port and process the data
	received.

	optional arguments:
	  -h, --help            show this help message and exit
	  --config-dir <config_dir>
	                        The location of the config directory, default:
	                        /etc/SerialGrabber


	#~> serial_grabber --config-dir /etc/SerialGrabber