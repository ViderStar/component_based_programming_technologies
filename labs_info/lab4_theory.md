# Lab 4: Jython

## Idea

**Jython** is Python 2.7 compiled to Java bytecode and run on the JVM. A Jython program imports Java classes as if they were Python modules, calls their methods, and can extend them; the opposite direction (Java running Python code) is a library call. The lab is about this Java ⇄ Python interaction.

## Terms

| Term | Meaning |
| --- | --- |
| `jython-standalone-2.7.3.jar` | interpreter and standard library in one jar: `java -jar jython-standalone.jar script.py` |
| `from java.io import File` | a Java class imported like a Python name |
| `class MyClass(Object)` | a Python class that extends a Java class; instances are Java objects |
| `sys.path.append("x.jar")` | puts a jar on the import path, so its classes can be imported |
| `PythonInterpreter` | the Java class that runs Python code inside a Java program |
| Swing | the Java GUI toolkit: `JFrame`, `JMenuBar`, `JPanel`, `paintComponent` |

## The handout examples (all in `lab4/jython/`)

| File | Example |
| --- | --- |
| `java_version.py` | `System.getProperty("java.version")`, `currentTimeMillis()` |
| `hello_world.py` | `sys.stdout.write` and `print` |
| `files_demo.py` | `File`, `FileWriter`, `IOException` |
| `my_class.py` | `class MyClass(Object)` |
| `greet_frame.py` | `JFrame` + `ActionListener` with Greet and Clear buttons |
| `image_viewer.py` | `ImageIO.read` and a `JComponent` that draws a JPEG |
| `array_list.py`, `call_java_class.py`, `draw_image.py`, `jy10.py` + `JythonHelloWorld.java` | examples of the lecture: collections, a Java class from a jar, drawing into a `BufferedImage`, Python run from Java |

## The task: the menu application

`lab4/jython/menu_app.py`: a `JFrame` with the menu bar **File / Draw / Help**. The Draw menu has *Picture 1* (a JPEG), *Picture 2* (a PNG), *Sine wave* and *Clear*. A `Canvas(JPanel)` overrides `paintComponent`: it scales the picture into the panel, or draws the axes, the grid and `y = sin(x)` on `[0, 4π]` with `Graphics2D`. One `Controller(ActionListener)` receives the events of all items and dispatches on the action command.

The menu bar, canvas and status line are installed into a `JRootPane`, which a `JFrame` owns but which also exists without a window. That allows `--snapshot`, which draws the content into a PNG without a display, and lets the tests check pixels.

## Things that differ from the handout (JDK 8 → 17)

- `import javax.swing as swing` fails with *No module named swing*: since Java 9 the classes are in modules and Jython's package scanner no longer lists them, although `from javax.swing import JFrame` works. `lab4/jython/jcompat.py` registers the packages with `sys.add_package`.
- The protected `paintComponent` of the superclass is called as `self.super__paintComponent(g)`, not `JPanel.paintComponent(self, g)`.
- The code is Python 2: `print` needs `from __future__ import print_function`, text with non-ASCII characters needs `u""` literals and `-Dfile.encoding=UTF-8`.
- A `JFrame` cannot be created when `java.awt.headless=true`, so everything that is checked automatically sits on `JPanel` and `JRootPane`.

## Links

- **Lab 1 extra (reflection)**: Java sent a method name to Python over a socket; here both live in one process and Jython resolves the names itself.
- **Lab 3 (Brython)**: the other place where Python runs inside a host runtime.
