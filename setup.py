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
import glob

requires=[
    "requests",
    "pyserial",
]

from setuptools import setup, find_packages

setup(name='SerialGrabber',
    version='0.0.1',
    description='SerialGrabber reads data from a serial port and processes it with the configured processor.',
    author='NigelB',
    author_email='nigel.blair@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    install_requires=requires,
    entry_points={
        "console_scripts": [
            "serial_grabber = serial_grabber.SerialGrabber:main",
        ]
    },
    data_files=[
        ("/etc/SerialGrabber", glob.glob("example_config/*"))
    ]
)