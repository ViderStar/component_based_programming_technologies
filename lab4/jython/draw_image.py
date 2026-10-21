# -*- coding: utf-8 -*-
"""Lecture example: draw on a BufferedImage with Graphics2D and save it. Usage: draw_image.py [out.png]"""
from __future__ import print_function

import sys

import jcompat  # noqa: F401  (registers the Swing packages, see jcompat.py)
import java.awt as awt
import java.awt.image as image
import java.io as io
import javax.imageio as imageio

# Create a new image with the desired dimensions
width = 200
height = 200
bufferedImage = image.BufferedImage(width, height, image.BufferedImage.TYPE_INT_RGB)

# Get the Graphics2D object to draw on the image
graphics = bufferedImage.createGraphics()

# Set the background color
graphics.setColor(awt.Color.WHITE)
graphics.fillRect(0, 0, width, height)

# Set the pen color
graphics.setColor(awt.Color.RED)

# Draw a rectangle
graphics.drawRect(50, 50, 100, 100)

# Draw an oval
graphics.drawOval(75, 75, 50, 50)

# Dispose of the Graphics2D object
graphics.dispose()

target = sys.argv[1] if len(sys.argv) > 1 else "drawn.png"
imageio.ImageIO.write(bufferedImage, "png", io.File(target))
print("saved " + target + ": " + str(width) + "x" + str(height))
