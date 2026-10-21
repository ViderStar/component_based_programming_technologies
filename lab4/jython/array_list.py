# -*- coding: utf-8 -*-
"""Lecture example: a Java collection is used from Python and iterated with a Python for loop."""
from __future__ import print_function

from java.util import ArrayList

# Create an instance of the ArrayList class
my_list = ArrayList()

# Add some elements to the list
my_list.add("Hello")
my_list.add("world")

# Print the contents of the list
for item in my_list:
    print(item)

print("size from Java: " + str(my_list.size()) + ", len() from Python: " + str(len(my_list)))
