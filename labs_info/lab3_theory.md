# Lab 3: wxPython components

## Idea

A component GUI is assembled from stock parts: button, toolbar, browser, calendar. wxPython wraps wxWidgets (native look on macOS, Windows, Linux). The handout asks for a toolbar with icons, tooltips, image and music loading, a browser, Word/Excel, calendar/clock, and PDF.

## Toolkit

- windows and dialogs, including `wx.FileDialog`
- buttons, fields, lists, trees, notebook
- menus and **toolbar**
- images
- events: `EVT_BUTTON`, `EVT_TOOL`
- custom widgets via **subclassing** (`CustomButton(wx.Button)`)

## Toolbar hints

```python
toolbar.AddTool(id, "Image", bitmap, "Load and show an image")
```

The fourth argument is the hover tooltip — required by the assignment.

Icons live in `assets/icons/` (PNG 128×128, shown at 32×32).

## Custom widget

`lab3.widgets.CustomButton` sets BSUIR colours and a tooltip, matching the red-button example in the handout.

## Browser

`wx.html2.WebView` opens `https://www.google.com`. That replaces ActiveX `InternetExplorer.Application` (no IE on macOS). If WebView is missing, the system browser is used.

## Media, Office, PDF

| Task | Implementation |
| --- | --- |
| Image | file dialog + Pillow → `wx.StaticBitmap` (WebP too) |
| Music | `pygame.mixer`, fallback `afplay` on macOS |
| Word | `open -a "Microsoft Word"` → Pages → TextEdit |
| Excel | Microsoft Excel → Numbers |
| Calendar / clock | `wx.adv.CalendarCtrl` + timer, plus Calendar.app |
| PDF | `pypdf` extracts text, `open` launches Preview |

On Windows: `os.startfile` and `winword`/`excel`. `win32com` examples stay in the report, not in macOS runtime.

## Layout

Widgets go into `wx.BoxSizer` / `wx.FlexGridSizer`, not absolute coordinates.

## Links

The course launcher and Labs 1, 2, 4 reuse the same wx theme. Lab 3 is the full multimedia stand from the handout.
