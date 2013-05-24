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
import logging

import re
from serial_grabber import cache


logger = logging.getLogger("cache")

def matches(pattern):
    pat = re.compile(pattern)
    def matches_impl(state, config, data):
        return pat.match(data)
    return matches_impl

def set_url(url):
    return None

def send_data():
    return None

def begin_transaction(_state):
    def b_trans_impl(state, config, data):
        try:
            state.data = []
#            state.data.append(data)   # Not needed because the catchall matcher below will catch it
            state.match_all = matches(".*")
            _state[state.match_all] = lambda state_, config_, data_: state_.data.append(data_)
        except Exception, e:
            import traceback
            traceback.print_exc()

    return b_trans_impl

def format_data(data, _del="\n"):
    return _del.join(data)

def end_transaction(_state):
    def e_trans_impl(state, config, data):
        try:
            if "match_all" in state: del _state[state.match_all]
            state.data.append(data)
            cache.cache(cache.make_payload(format_data(state.data)))
            del state["data"]
            logger.info("End of Transaction")
        except Exception, e:
            import traceback
            traceback.print_exc()

    return e_trans_impl

