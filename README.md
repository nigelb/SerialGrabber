SerialGrabber has the following dependencies:

 * pyserial
 * requests
 * ppygtk

Instilation:
	
	#> python setup.py install

This will create a deafult configuration in /etc/SerialGrabber:

* SerialGrabber_Cache.py - Configure the cache function handles




To configure it, edit it and specify the serial connection parameters
and the server to which the data is posted.

This is a new implementation that caches and archives the data to the local
disk. Ensuring that less data is lost due to network issues etc.


Ensure you have the configuration in settings.py set correctly.
