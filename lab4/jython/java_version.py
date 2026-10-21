# -*- coding: utf-8 -*-
"""Handout example 1: Java classes are imported into Python code (first.py of the handout)."""
from __future__ import print_function

import sys

from java.lang import System  # Java import

print('Running on Java version: ' + System.getProperty('java.version'))
print('Unix time from Java: ' + str(System.currentTimeMillis()))
print('Jython version: ' + sys.version.split()[0])
