#!/usr/bin/env python
# SerialGrabber reads data from a serial port and processes it with the
# configured processor.
# Copyright (C) 2012  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import os, sys, cgitb


def error(code, message, content_type="text/plain"):
    print "Status:%s"%code
    print "Content-Type: %s"%content_type
    print "Content-Length: %s"%len(message)
    print""
    print "HTTP/1.1 %s Service Unavailable"%code
    sys.stderr.write(message)
    sys.exit(code)

if __name__ == "__main__":



    if "SERIAL_GRABBER_PYTHON_PATH_INCLUDE" in os.environ:
        sys.path.append(os.environ["SERIAL_GRABBER_PYTHON_PATH_INCLUDE"])

    from serial_grabber.commander.cgi.cgi_constants import SERIAL_GRABBER_CONFIG_DIR, SERIAL_GRABBER_ENABLE_CGITB, SERIAL_GRABBER_CGI_PREFIX
    from serial_grabber.util import config_helper
    config = config_helper({})

    if SERIAL_GRABBER_CONFIG_DIR not in os.environ:
        error(503, """The environment variable %s needs to bet to the directory containing the SerialGrabber configuration.
For Apache servers, set the "SetEnv" directive.
"""%SERIAL_GRABBER_CONFIG_DIR)



    if SERIAL_GRABBER_CGI_PREFIX in os.environ:
        config.SERIAL_GRABBER_CGI_PREFIX = os.environ[SERIAL_GRABBER_CGI_PREFIX]
    else:
        config.SERIAL_GRABBER_CGI_PREFIX = None
    sys.path.append(os.environ[SERIAL_GRABBER_CONFIG_DIR])

    from SerialGrabber_CGI import cgi_handler


    if SERIAL_GRABBER_ENABLE_CGITB in os.environ and os.environ[SERIAL_GRABBER_ENABLE_CGITB].lower() == "true":
        cgitb.enable()
        config.SERIAL_GRABBER_ENABLE_CGITB = True
    else:
        config.SERIAL_GRABBER_ENABLE_CGITB = False


    cgi_handler(config).handle()