#!/usr/bin/env python
# SerialGrabber reads data from a serial port and processes it with the
# configured processor.
#
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

#from gui import start
from argparse import ArgumentParser

import logging, os, sys

def main():
    argParse = ArgumentParser(description="Serial Grabber will read the configured serial port and process the data received.")
    argParse.add_argument("--config-dir",metavar="<config_dir>", dest="config_dir", default="/etc/SerialGrabber", action="store", help="The location of the config directory, default: /etc/SerialGrabber")
    args = argParse.parse_args()

    args.config_dir = os.path.abspath(args.config_dir)
    sys.path.append(args.config_dir)

    try:
        import SerialGrabber_Paths, SerialGrabber_Settings, SerialGrabber_UI
    except ImportError, e:
        print "Could not find configuration in %s, specify with --config-dir option."%(args.config_dir)
        exit(1)
        #Ensure the directories exist.
    if SerialGrabber_Paths.data_logger_dir is not None:
        if not os.path.exists(SerialGrabber_Paths.data_logger_dir):
            os.makedirs(SerialGrabber_Paths.data_logger_dir)
        if not os.path.exists(SerialGrabber_Paths.cache_dir):
            os.makedirs(SerialGrabber_Paths.cache_dir)
        if not os.path.exists(SerialGrabber_Paths.archive_dir):
            os.makedirs(SerialGrabber_Paths.archive_dir)

    #Setup up the logging
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
    log_file =  os.path.join(SerialGrabber_Paths.data_logger_dir, "datalogger.log")

#    logging.basicConfig(format=FORMAT,level=logging.INFO, filename=log_file)
    logging.basicConfig(format=FORMAT,level=logging.INFO)

#    hdlr = logging.StreamHandler(sys.stderr)
#    hdlr.setFormatter(logging.Formatter(FORMAT))
#    hdlr.setLevel(logging.NOTSET)
#    logging.root.addHandler(hdlr)

    logger = logging.getLogger("Main")
    commander = None
    if "commander" in SerialGrabber_Settings.__dict__:
        commander = SerialGrabber_Settings.commander

    reader = None
    if "reader" in SerialGrabber_Settings.__dict__:
        reader = SerialGrabber_Settings.reader

    processor = None
    if "processor" in SerialGrabber_Settings.__dict__:
        processor = SerialGrabber_Settings.processor

    SerialGrabber_UI.ui.start(logger, reader, processor, commander)

if __name__ == "__main__":
    main()



