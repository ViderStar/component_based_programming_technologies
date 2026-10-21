# -*- coding: utf-8 -*-
"""Handout example: display a JPEG in a Swing component.

Usage: image_viewer.py path/to/picture.jpg [--info]
`--info` only reads the file and prints its size, without a window.
"""
from __future__ import print_function

import sys

import jcompat  # noqa: F401  (registers the Swing packages, see jcompat.py)
import java.awt as awt
import java.io as io
import javax.imageio as imageio
import javax.swing as swing

# Load the JPEG image from file
image_file = io.File(sys.argv[1])
image = imageio.ImageIO.read(image_file)

if "--info" in sys.argv:
    print("image " + image_file.getName() + ": " + str(image.getWidth()) + "x" + str(image.getHeight()))
    sys.exit(0)


# Create a Swing component to display the image
class ImageComponent(swing.JComponent):
    def __init__(self, image):
        self.image = image
        self.setPreferredSize(awt.Dimension(image.getWidth(), image.getHeight()))

    def paintComponent(self, g):
        g.drawImage(self.image, 0, 0, None)


# Create a JFrame to hold the image component
frame = swing.JFrame("Image Example")
frame.setDefaultCloseOperation(swing.JFrame.EXIT_ON_CLOSE)

# Create an instance of the image component
image_component = ImageComponent(image)

# Add the image component to the frame
frame.getContentPane().add(image_component)

# Set the size of the frame and display it
frame.pack()
frame.setVisible(True)
