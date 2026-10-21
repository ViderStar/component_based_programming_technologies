# -*- coding: utf-8 -*-
"""Lab 4 task: a Jython application with a visual Java class, a JFrame whose menu draws on a canvas.

The Draw menu has three items: load the first picture, load the second picture, draw a sine wave.

    jython menu_app.py                      open the window
    jython menu_app.py --view sine          open it with a view already chosen (picture1, picture2, sine)
    jython menu_app.py --snapshot out.png --view sine [--size 640x400] [--frame [--popup Draw]]
                                            draw into a PNG instead of the screen, without a display:
                                            the canvas alone, or with --frame the menu bar, canvas and
                                            status line (--popup opens one menu in the picture)
    jython menu_app.py --selftest           press every menu item programmatically and print the outcome
"""
from __future__ import print_function

import math
import os
import sys

from java.awt import BasicStroke, BorderLayout, Color, Container, Dimension, Font, RenderingHints, Toolkit
from java.awt.event import ActionListener, InputEvent, KeyEvent
from java.awt.geom import Path2D
from java.awt.image import BufferedImage
from java.io import File
from java.lang import System, Throwable
from javax.imageio import ImageIO
from javax.swing import (BorderFactory, JFrame, JLabel, JMenu, JMenuBar, JMenuItem, JOptionPane, JPanel,
                         JRootPane, KeyStroke, SwingUtilities)

HERE = os.path.dirname(os.path.abspath(__file__))
PICTURES_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "lab4"))
PICTURES = {
    "picture1": os.path.join(PICTURES_DIR, "picture1.jpg"),
    "picture2": os.path.join(PICTURES_DIR, "picture2.png"),
}
BLUE = Color(0, 85, 165)
NAVY = Color(12, 36, 68)
GREY = Color(138, 151, 168)
LIGHT = Color(230, 235, 242)
TITLE = "Jython: menu, two pictures and a sine wave"


class Canvas(JPanel):
    """The drawing area: a Java JPanel whose paintComponent is written in Python."""

    PERIODS = 2  # the sine wave covers [0, 2 * 2*pi]

    def __init__(self):
        JPanel.__init__(self)
        self.setBackground(Color.WHITE)
        self.setPreferredSize(Dimension(640, 400))
        self.mode = "empty"
        self.image = None
        self.caption = ""
        self.image_box = None

    def show_picture(self, path):
        self.image = ImageIO.read(File(path))  # Java ImageIO decodes JPEG and PNG alike
        self.caption = os.path.basename(path)
        self.mode = "picture"
        self.repaint()

    def show_sine(self):
        self.mode = "sine"
        self.caption = "y = sin(x), x from 0 to " + str(2 * self.PERIODS) + "*pi"
        self.repaint()

    def clear(self):
        self.mode = "empty"
        self.image = None
        self.caption = ""
        self.repaint()

    def paintComponent(self, g):
        self.super__paintComponent(g)  # let Swing paint the background first (protected Java method)
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
        width, height = self.getWidth(), self.getHeight()
        if self.mode == "picture":
            self.draw_picture(g, width, height)
        elif self.mode == "sine":
            self.draw_sine(g, width, height)
        else:
            g.setColor(GREY)
            g.setFont(Font("SansSerif", Font.PLAIN, 14))
            g.drawString(u"Open the Draw menu and choose a picture or the sine wave", 24, height // 2)

    def draw_picture(self, g, width, height):
        """The picture is scaled to fit and centred; its box is remembered for the tests."""
        margin = 12
        scale = min((width - 2 * margin) / float(self.image.getWidth()),
                    (height - 2 * margin) / float(self.image.getHeight()))
        w, h = int(self.image.getWidth() * scale), int(self.image.getHeight() * scale)
        x, y = (width - w) // 2, (height - h) // 2
        g.drawImage(self.image, x, y, w, h, None)
        g.setColor(GREY)
        g.drawRect(x - 1, y - 1, w + 1, h + 1)
        self.image_box = (x, y, w, h)

    def sine_frame(self, width, height):
        """Plot area (left, top, width, height) in pixels."""
        return 56, 24, width - 56 - 24, height - 24 - 44

    def draw_sine(self, g, width, height):
        left, top, w, h = self.sine_frame(width, height)
        x_max = 2 * math.pi * self.PERIODS
        y_max = 1.2

        def px(x):
            return left + x / x_max * w

        def py(y):
            return top + h / 2.0 - y / y_max * h / 2.0

        g.setFont(Font("SansSerif", Font.PLAIN, 12))
        # grid and tick labels: multiples of pi on x, -1, 0, 1 on y
        g.setStroke(BasicStroke(1.0))
        for k in range(0, 4 * self.PERIODS + 1):
            x = px(k * math.pi / 2)
            g.setColor(LIGHT if k % 2 else GREY)
            g.drawLine(int(x), top, int(x), top + h)
            if k % 2 == 0:
                label = u"0" if k == 0 else (u"π" if k == 2 else u"%dπ" % (k // 2))
                g.setColor(NAVY)
                g.drawString(label, int(x) - 4, top + h + 18)
        for value in (-1, 0, 1):
            y = py(value)
            g.setColor(GREY if value == 0 else LIGHT)
            g.drawLine(left, int(y), left + w, int(y))
            g.setColor(NAVY)
            g.drawString(u"%d" % value, left - 18, int(y) + 4)
        g.setColor(GREY)
        g.drawRect(left, top, w, h)

        # the curve: one segment per pixel column
        path = Path2D.Double()
        for i in range(w + 1):
            x = x_max * i / float(w)
            if i == 0:
                path.moveTo(px(x), py(math.sin(x)))
            else:
                path.lineTo(px(x), py(math.sin(x)))
        g.setColor(BLUE)
        g.setStroke(BasicStroke(2.5, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND))
        g.draw(path)
        g.setStroke(BasicStroke(1.0))
        g.setColor(NAVY)
        g.setFont(Font("SansSerif", Font.BOLD, 13))
        g.drawString(u"y = sin(x)", left + 8, top + 18)


class Controller(ActionListener):
    """Reacts to the menu: one object listens to every item and dispatches by the action command."""

    def __init__(self, canvas, status=None, frame=None):
        self.canvas = canvas
        self.status = status
        self.frame = frame
        self.log = []

    def say(self, text):
        self.log.append(text)
        if self.status is not None:
            self.status.setText(u"  " + text)

    def actionPerformed(self, event):
        command = event.getActionCommand()
        if command in PICTURES:
            self.canvas.show_picture(PICTURES[command])
            self.say(u"Loaded " + self.canvas.caption + u" (" + str(self.canvas.image.getWidth()) + u"x"
                     + str(self.canvas.image.getHeight()) + u")")
        elif command == "sine":
            self.canvas.show_sine()
            self.say(u"Drew a sine wave")
        elif command == "clear":
            self.canvas.clear()
            self.say(u"Canvas cleared")
        elif command == "about":
            self.say(u"About")
            if self.frame is not None:
                JOptionPane.showMessageDialog(self.frame, u"Lab 4. Jython + Swing\nArtsem Lebiadzevich, BSUIR, 2026")
        elif command == "exit":
            if self.frame is not None:
                self.frame.dispose()
            self.say(u"Exit")


def shortcut(key):
    """Cmd+key on macOS, Ctrl+key elsewhere."""
    try:
        mask = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()  # Java 10+, needs a non-headless toolkit
    except (Exception, Throwable):
        on_mac = "mac" in System.getProperty("os.name").lower()
        mask = InputEvent.META_DOWN_MASK if on_mac else InputEvent.CTRL_DOWN_MASK
    return KeyStroke.getKeyStroke(key, mask)


def make_item(title, command, listener, key=None):
    item = JMenuItem(title)
    item.setActionCommand(command)
    item.addActionListener(listener)
    if key is not None:
        item.setAccelerator(shortcut(key))
    return item


def build_menu_bar(listener):
    bar = JMenuBar()
    file_menu = JMenu("File")
    file_menu.add(make_item("Exit", "exit", listener, KeyEvent.VK_Q))
    bar.add(file_menu)

    draw_menu = JMenu("Draw")
    draw_menu.add(make_item("Picture 1 (JPEG)", "picture1", listener, KeyEvent.VK_1))
    draw_menu.add(make_item("Picture 2 (PNG)", "picture2", listener, KeyEvent.VK_2))
    draw_menu.add(make_item(u"Sine wave", "sine", listener, KeyEvent.VK_3))
    draw_menu.addSeparator()
    draw_menu.add(make_item("Clear", "clear", listener, KeyEvent.VK_0))
    bar.add(draw_menu)

    help_menu = JMenu("Help")
    help_menu.add(make_item("About", "about", listener))
    bar.add(help_menu)
    return bar


def install(root, controller, canvas, status):
    """Menu bar, canvas and status line go into a root pane; a JFrame owns one, and so can a snapshot."""
    root.setJMenuBar(build_menu_bar(controller))
    root.getContentPane().add(canvas, BorderLayout.CENTER)
    root.getContentPane().add(status, BorderLayout.SOUTH)


def make_status():
    status = JLabel(u"  Choose an item in the Draw menu")
    status.setBorder(BorderFactory.createEmptyBorder(4, 4, 4, 4))
    return status


class MenuFrame(JFrame):
    """The window: a menu bar, the canvas in the centre and a status line."""

    def __init__(self, visible=True):
        JFrame.__init__(self, TITLE)
        self.canvas = Canvas()
        self.status = make_status()
        self.controller = Controller(self.canvas, self.status, self)
        install(self.getRootPane(), self.controller, self.canvas, self.status)
        self.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE)
        self.pack()
        self.setLocationRelativeTo(None)
        self.setVisible(visible)


# ------------------------------------------------------------------ command line


def parse_args(argv):
    options = {"view": None, "snapshot": None, "size": (640, 400), "frame": False, "popup": None, "selftest": False}
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("--view", "--snapshot", "--size", "--popup"):
            i += 1
            value = argv[i]
            if arg == "--size":
                value = tuple(int(part) for part in value.lower().split("x"))
            options[arg[2:]] = value
        elif arg == "--frame":
            options["frame"] = True
        elif arg == "--selftest":
            options["selftest"] = True
        else:
            raise SystemExit("unknown argument: " + arg)
        i += 1
    return options


def apply_view(controller, view):
    if view is None or view == "empty":
        return
    controller.actionPerformed(_Command(view))


class _Command(object):
    """Stands in for an ActionEvent when the view is chosen from the command line."""

    def __init__(self, command):
        self.command = command

    def getActionCommand(self):
        return self.command


def layout_tree(component):
    """Lay out a component tree that has no window (no peer, so validate() would do nothing)."""
    component.doLayout()
    if isinstance(component, Container):
        for child in component.getComponents():
            layout_tree(child)


def render(component, width, height):
    image = BufferedImage(width, height, BufferedImage.TYPE_INT_RGB)
    g = image.createGraphics()
    g.setColor(Color.WHITE)
    g.fillRect(0, 0, width, height)
    component.paint(g)
    return image, g


def snapshot(options):
    """Draw into a PNG without a display: the canvas alone, or with --frame the whole window content."""
    width, height = options["size"]
    path = options["snapshot"]
    canvas = Canvas()
    if options["frame"]:
        canvas.setPreferredSize(Dimension(width, height))
        status = make_status()
        controller = Controller(canvas, status)
        root = JRootPane()
        install(root, controller, canvas, status)
        apply_view(controller, options["view"])
        size = root.getPreferredSize()
        root.setSize(size)
        layout_tree(root)
        image, g = render(root, size.width, size.height)
        if options["popup"]:
            bar = root.getJMenuBar()
            for index in range(bar.getMenuCount()):
                menu = bar.getMenu(index)
                if menu.getText() == options["popup"]:
                    popup = menu.getPopupMenu()
                    popup.setSize(popup.getPreferredSize())
                    layout_tree(popup)
                    corner = SwingUtilities.convertPoint(menu, 0, menu.getHeight(), root)
                    g.translate(corner.x, corner.y)
                    popup.paint(g)
    else:
        controller = Controller(canvas)
        apply_view(controller, options["view"])
        canvas.setSize(width, height)
        image, g = render(canvas, width, height)
    g.dispose()
    ImageIO.write(image, "png", File(path))
    print("snapshot " + path + ": " + str(image.getWidth()) + "x" + str(image.getHeight()) + ", view " + canvas.mode)
    if canvas.image_box is not None:
        print("image box: " + " ".join(str(v) for v in canvas.image_box))


def selftest():
    """Press every menu item the way a user would and report the canvas state after each press."""
    canvas = Canvas()
    controller = Controller(canvas)
    bar = build_menu_bar(controller)
    draw = bar.getMenu(1)
    print("menus: " + ", ".join(bar.getMenu(i).getText() for i in range(bar.getMenuCount())))
    print("Draw items: " + ", ".join(draw.getItem(i).getText() for i in range(draw.getItemCount())
                                     if draw.getItem(i) is not None))
    for index, expected in ((0, "picture"), (1, "picture"), (2, "sine"), (4, "empty")):
        item = draw.getItem(index)
        item.doClick(0)
        print("click '" + item.getText() + "' -> mode " + canvas.mode + ", caption '" + canvas.caption + "'")
        assert canvas.mode == expected, (item.getText(), canvas.mode)
    print("status log: " + " | ".join(controller.log))
    print("selftest ok")


def main(argv):
    options = parse_args(argv)
    if options["selftest"]:
        selftest()
    elif options["snapshot"]:
        snapshot(options)
    else:
        System.setProperty("apple.laf.useScreenMenuBar", "false")  # keep the menu inside the window on macOS
        frame = MenuFrame()
        apply_view(frame.controller, options["view"])
        return
    System.exit(0)  # AWT keeps the JVM alive for a moment after the last window is gone


if __name__ == "__main__":
    main(sys.argv)
