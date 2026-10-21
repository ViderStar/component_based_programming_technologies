# -*- coding: utf-8 -*-
"""Lecture example: a user-defined Java class (com.MyClass) from a jar is imported into Jython.

Usage: call_java_class.py path/to/myclass.jar
"""
from __future__ import print_function

import sys

# Add the JAR file to the classpath
sys.path.append(sys.argv[1])

# Now the classes of the jar are importable
from com import MyClass

my_object = MyClass()
print(my_object.hello("oleg"))
print("static call: " + MyClass.hello("Jython"))
