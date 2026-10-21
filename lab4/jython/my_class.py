# -*- coding: utf-8 -*-
"""Handout example 4: a Python class that extends the Java class java.lang.Object."""
from __future__ import print_function

from java.lang import Object


class MyClass(Object):
    def __init__(self):
        Object.__init__(self)
        self.message = "Hello, world! Form Class"

    def printMessage(self):
        print(self.message)


z = MyClass()
z.printMessage()

# the object is a Java object: Java methods and instanceof work on it
print("isinstance(z, Object): " + str(isinstance(z, Object)))
print("hashCode is stable: " + str(z.hashCode() == z.hashCode()))
print("Java superclass: " + z.getClass().getSuperclass().getName())
