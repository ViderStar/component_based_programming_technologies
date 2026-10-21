# -*- coding: utf-8 -*-
"""Handout example 2: "Hello, world!" through sys.stdout, and the same with print."""
from __future__ import print_function

# import the sys module to access stdout
import sys


# define a function that prints a message to stdout
def print_message(message):
    sys.stdout.write(message + "\n")


# call the print_message function with the "Hello, world!" message
print_message("Hello, world!")


# Python code: gives the same result
def greet(name):
    print("Hello, " + name + "!")


greet("Oleg")
