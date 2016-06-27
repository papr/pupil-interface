'''
(*)~----------------------------------------------------------------------------
Pupil Interface - A simple interface to control Pupil applications
Copyright (C) 2016 Pablo Prietz

Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------~(*)
'''

__version__ = '0.2'

import utils
import zmq_tools
from .communicator import Communicator

__all__ = ['Communicator','utils','zmq_tools']