"""Lab 5 window: the JSP application served by Tomcat in a web view next to the checklist of cases."""

from __future__ import annotations

import wx
import wx.html2

from helpers.office import open_path
from lab5 import cases, runtime
from ui.cases import CasePanel
from ui.theme import MUTED, PAGE_BG, apply_window_icon, make_header, styled_button

PAGES = [
    ("Home", "index.jsp", ""),
    ("Prototype", "response.jsp", "?name=Oleg"),
    ("Currency", "rate.jsp", "?name=dollar"),
    ("Image", "image.html", ""),
    ("Translator", "translate.jsp", "?word=hello"),
    ("Site", "site.jsp", "?page=labs"),
]


class Lab5Frame(wx.Frame):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Lab 5", size=(1280, 760))
        apply_window_icon(self)
        root = wx.Panel(self)
        root.SetBackgroundColour(PAGE_BG)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(make_header(root, "Lab 5  JSP"), 0, wx.EXPAND)

        body = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        row = wx.BoxSizer(wx.HORIZONTAL)
        for title, page, query in PAGES:
            button = styled_button(root, title, primary=page != "index.jsp")
            button.Bind(wx.EVT_BUTTON, lambda _e, p=page, q=query: self.open_page(p, q))
            row.Add(button, 0, wx.RIGHT, 6)
        row.AddStretchSpacer()
        external = styled_button(root, "Open in browser", primary=False)
        external.Bind(wx.EVT_BUTTON, lambda _e: open_path(cases.ensure_server().url))
        row.Add(external, 0)
        left.Add(row, 0, wx.EXPAND | wx.BOTTOM, 8)

        self.url_label = wx.StaticText(root, label="")
        self.url_label.SetForegroundColour(MUTED)
        left.Add(self.url_label, 0, wx.BOTTOM, 6)
        try:
            self.browser: wx.html2.WebView | None = wx.html2.WebView.New(root)
        except Exception:
            self.browser = None
        if self.browser is not None:
            left.Add(self.browser, 1, wx.EXPAND)
        else:
            left.Add(wx.StaticText(root, label="No web view available: use “Open in browser”."), 1)
        body.Add(left, 1, wx.EXPAND | wx.ALL, 8)

        self.cases = CasePanel(
            root,
            [
                ("Tomcat + Java", cases.environment),
                ("war build", cases.war_build),
                ("TODAY IS page", cases.today_page),
                ("prototype bean", cases.hello_prototype),
                ("currency rates", cases.currency_rates),
                ("image from JSP", cases.image_png),
                ("translator", cases.translator),
                ("site via PrintWriter", cases.site_writer),
            ],
        )
        body.Add(self.cases, 0, wx.EXPAND | wx.ALL, 8)
        layout.Add(body, 1, wx.EXPAND)
        root.SetSizer(layout)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Centre()
        self.open_page("index.jsp")

    def open_page(self, page: str, query: str = "") -> None:
        try:
            url = cases.ensure_server().page(page, query)
        except (OSError, RuntimeError, runtime.TomcatUnavailable) as exc:
            self.url_label.SetLabel(f"Tomcat: {exc}".splitlines()[0])
            return
        self.url_label.SetLabel(url)
        if self.browser is not None:
            self.browser.LoadURL(url)

    def _on_close(self, event: wx.CloseEvent) -> None:
        cases.stop_server()
        event.Skip()
