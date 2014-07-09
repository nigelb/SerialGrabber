SerialGrabber has the following dependencies:

 * pyserial
 * requests
 * ppygtk - if using the gui ui (opposed the cli ui)

Instilation:
	
	#> python setup.py install

This will create a deafult configuration in /etc/SerialGrabber:

* [`SerialGrabber_Cache.py`](example_config/SerialGrabber_Cache.py) - Configure the cache/archive function handlers
* [`SerialGrabber_Calibration.py`](example_config/SerialGrabber_Calibration.py) - Configure Calibration providers
* [`SerialGrabber_Paths.py`](example_config/SerialGrabber_Paths.py) - Configure the logging, data, and cache directories
* [`SerialGrabber_Settings.py`](example_config/SerialGrabber_Settings.py) - Configure the reader (i.e serial port) and processors (i.e. uploader)
* [`SerialGrabber_State.py`](example_config/SerialGrabber_State.py) - Configure the reader parsing state tables
* [`SerialGrabber_UI.py`](example_config/SerialGrabber_UI.py) - Select the UI to use: eg. cli


