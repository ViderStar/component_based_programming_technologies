# -*- coding: utf-8 -*-
"""Handout example: a visual class, a JFrame that is its own ActionListener.

`--selftest` builds the frame, presses both buttons programmatically and prints what happened.
"""
from __future__ import print_function

import sys

from java.awt.event import ActionListener
from javax.swing import JFrame, JButton, JLabel, JTextField, JPanel, BoxLayout


class MyFrame(JFrame, ActionListener):
    def __init__(self, visible=True):
        JFrame.__init__(self, "My Frame")

        # Set the layout manager
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.PAGE_AXIS))

        # Create a panel for the input fields
        input_panel = JPanel()
        input_panel.setLayout(BoxLayout(input_panel, BoxLayout.LINE_AXIS))
        input_panel.add(JLabel("Enter your name: "))
        self.name_field = JTextField()
        input_panel.add(self.name_field)

        # Create a panel for the buttons
        button_panel = JPanel()
        button_panel.setLayout(BoxLayout(button_panel, BoxLayout.LINE_AXIS))
        self.greet_button = JButton("Greet")
        self.greet_button.addActionListener(self)
        button_panel.add(self.greet_button)
        self.clear_button = JButton("Clear")
        self.clear_button.addActionListener(self)
        button_panel.add(self.clear_button)

        # Add the panels to the frame
        self.add(input_panel)
        self.add(button_panel)

        # Set the size of the frame and make it visible
        self.setSize(300, 200)
        self.setVisible(visible)

    def actionPerformed(self, event):
        if event.getSource() == self.greet_button:
            name = self.name_field.getText()
            if name:
                print("Hello, " + name + "!")
        elif event.getSource() == self.clear_button:
            self.name_field.setText("")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        frame = MyFrame(visible=False)
        frame.name_field.setText("Oleg")
        frame.greet_button.doClick()
        frame.clear_button.doClick()
        print("field after Clear: '" + frame.name_field.getText() + "'")
        frame.dispose()
    else:
        # Create an instance of the frame
        frame = MyFrame()
