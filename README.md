[Read the documentation.](http://serialgrabber.readthedocs.org/)

Quickly
-------

SerialGrabber has the following dependencies:

 * pyserial

Installation:
	
	#> python setup.py install

This will create a default configuration in /etc/SerialGrabber:

* [`SerialGrabber_Storage.py`](example_config/SerialGrabber_Storage.py) - Configure the storage (Cache and Archive) handlers
* [`SerialGrabber_Calibration.py`](example_config/SerialGrabber_Calibration.py) - Configure Calibration providers
* [`SerialGrabber_Paths.py`](example_config/SerialGrabber_Paths.py) - Configure the logging, data, and cache directories
* [`SerialGrabber_Settings.py`](example_config/SerialGrabber_Settings.py) - Configure the reader (i.e serial port) and processors (i.e. uploader)
* [`SerialGrabber_UI.py`](example_config/SerialGrabber_UI.py) - Select the UI to use: eg. cli


Commandline:

	#> serial_grabber --help
	usage: serial_grabber [-h] [--config-dir <config_dir>] [-v]

	Serial Grabber will read the configured serial port and process the data
	received.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --config-dir <config_dir>
	                        The location of the config directory, default:
	                        /etc/SerialGrabber
          -v, --verbosity       increase output verbosity
	
	
	#> serial_grabber --config-dir /etc/SerialGrabber


Out of the box SerialGrabber is quiet. To increase verbosity add additional `-v` arguments:


	#> serial_grabber --config-dir /etc/SerialGrabber -vvv


Serial Port Forwarding
----------------------
On the machine with the port you would like to forward:

    stty -F /dev/ttyttyUSB0 115200
    socat  open:/dev/ttyUSB0  tcp-listen:9999

On the machine you would like to access the port:

    socat tcp:localhost:9999 pty,raw,link=<serialport>
