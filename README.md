SerialGrabber has the following dependencies:

 * pyserial
 * requests
 * ppygtk - if using the gui ui (opposed the cli ui)

Instilation:
	
	#> python setup.py install

This will create a deafult configuration in /etc/SerialGrabber:

* `SerialGrabber_Cache.py` - Configure the cache function handles
* `SerialGrabber_Calibration.py` - Configure Calibration providers
* `SerialGrabber_Paths.py` - Configure the logging, data, and cache directories
* `SerialGrabber_Settings.py` - Configure the reader (i.e serial port) and processors (i.e. uploader)
* `SerialGrabber_State.py` - Configure the reader parsing state tables
* `SerialGrabber_UI.py` - Select the UI to use: eg. cli




To configure it, edit it and specify the serial connection parameters
and the server to which the data is posted.

This is a new implementation that caches and archives the data to the local
disk. Ensuring that less data is lost due to network issues etc.


Ensure you have the configuration in settings.py set correctly.
