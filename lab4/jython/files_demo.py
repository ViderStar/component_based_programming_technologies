# -*- coding: utf-8 -*-
"""Handout example 3: files and directories through java.io. Usage: files_demo.py [parent-directory]"""
from __future__ import print_function

import sys

from java.io import File, FileWriter, IOException

parent = File(sys.argv[1]) if len(sys.argv) > 1 else None

# Create a new directory
dir = File(parent, "example_dir") if parent is not None else File("example_dir")
dir.mkdir()

# Create a new file in the directory
file = File(dir, "example_file.txt")
try:
    file.createNewFile()
except IOException as e:
    print("An error occurred:", e)

# Write some text to the file
try:
    writer = FileWriter(file)
    writer.write("This is an example file.")
    writer.close()
except IOException as e:
    print("An error occurred:", e)

# Print a message to indicate that the file was written
print("The file", file.getAbsolutePath(), "has been written.")
