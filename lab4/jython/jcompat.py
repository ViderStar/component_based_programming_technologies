# -*- coding: utf-8 -*-
"""Makes the handout's `import javax.swing as swing` work on Jython 2.7.3 with JDK 9 or newer.

Since Java 9 the classes live in modules (java.desktop holds java.awt and javax.swing) and Jython's
package scanner no longer lists them, so `import java.awt as awt` raises "No module named awt" even
though `from java.awt import Color` works. Registering the package names fixes it; on JDK 8 the call
is harmless.
"""
import sys

PACKAGES = (
    "java.awt",
    "java.awt.event",
    "java.awt.geom",
    "java.awt.image",
    "javax.imageio",
    "javax.sound.sampled",
    "javax.swing",
)

for _package in PACKAGES:
    sys.add_package(_package)
