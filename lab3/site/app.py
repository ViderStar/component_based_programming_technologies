"""Page logic written in Python and run by Brython: DOM events, tables and canvas plots.

The numerical methods live in numerics.py, the same file that CPython imports in the tests.
"""

import json
import math
import sys

from browser import document, html, window

import numerics as nm

TABS = ["roots", "regression", "optimum"]
WIDTH, HEIGHT = 640, 420


# ---------------------------------------------------------------- helpers


def show_tab(name):
    for tab in TABS:
        if tab == name:
            document[tab].classList.add("on")
            document["tab_" + tab].classList.add("on")
        else:
            document[tab].classList.remove("on")
            document["tab_" + tab].classList.remove("on")


def fmt(value):
    return "{:.6g}".format(value)


def show_error(box, message):
    box.clear()
    box <= html.DIV(message, Class="error")


def nice_step(span, target=6):
    raw = span / target
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 5, 10):
        if raw <= factor * magnitude:
            return factor * magnitude
    return 10 * magnitude


def ticks(low, high):
    step = nice_step(high - low)
    value = math.ceil(low / step) * step
    out = []
    while value <= high + step * 1e-9:
        out.append(round(value / step) * step)
        value += step
    return out


class Plot:
    """Axes in data coordinates on a canvas 2D context."""

    def __init__(self, canvas_id, xmin, xmax, ymin, ymax):
        self.canvas = document[canvas_id]
        self.ctx = self.canvas.getContext("2d")
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.left, self.right, self.top, self.bottom = 48, 14, 14, 30
        self.ctx.fillStyle = "#ffffff"
        self.ctx.fillRect(0, 0, WIDTH, HEIGHT)

    def sx(self, x):
        return self.left + (x - self.xmin) / (self.xmax - self.xmin) * (WIDTH - self.left - self.right)

    def sy(self, y):
        return HEIGHT - self.bottom - (y - self.ymin) / (self.ymax - self.ymin) * (HEIGHT - self.top - self.bottom)

    def axes(self):
        ctx = self.ctx
        ctx.font = "11px sans-serif"
        ctx.lineWidth = 1
        for value in ticks(self.xmin, self.xmax):
            x = self.sx(value)
            ctx.strokeStyle = "#e6ebf2"
            ctx.beginPath()
            ctx.moveTo(x, self.top)
            ctx.lineTo(x, HEIGHT - self.bottom)
            ctx.stroke()
            ctx.fillStyle = "#5a687a"
            ctx.textAlign = "center"
            ctx.fillText(fmt(value), x, HEIGHT - self.bottom + 15)
        for value in ticks(self.ymin, self.ymax):
            y = self.sy(value)
            ctx.strokeStyle = "#e6ebf2"
            ctx.beginPath()
            ctx.moveTo(self.left, y)
            ctx.lineTo(WIDTH - self.right, y)
            ctx.stroke()
            ctx.fillStyle = "#5a687a"
            ctx.textAlign = "right"
            ctx.fillText(fmt(value), self.left - 6, y + 4)
        ctx.strokeStyle = "#8a97a8"
        ctx.strokeRect(self.left, self.top, WIDTH - self.left - self.right, HEIGHT - self.top - self.bottom)
        # the axes x = 0 and y = 0 when they are in view
        ctx.strokeStyle = "#5a687a"
        if self.xmin < 0 < self.xmax:
            ctx.beginPath()
            ctx.moveTo(self.sx(0), self.top)
            ctx.lineTo(self.sx(0), HEIGHT - self.bottom)
            ctx.stroke()
        if self.ymin < 0 < self.ymax:
            ctx.beginPath()
            ctx.moveTo(self.left, self.sy(0))
            ctx.lineTo(WIDTH - self.right, self.sy(0))
            ctx.stroke()

    def line(self, points, color, width=2):
        ctx = self.ctx
        ctx.strokeStyle = color
        ctx.lineWidth = width
        ctx.beginPath()
        for i, (x, y) in enumerate(points):
            if i == 0:
                ctx.moveTo(self.sx(x), self.sy(y))
            else:
                ctx.lineTo(self.sx(x), self.sy(y))
        ctx.stroke()
        ctx.lineWidth = 1

    def dot(self, x, y, color, radius=4, label=None):
        ctx = self.ctx
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(self.sx(x), self.sy(y), radius, 0, 2 * math.pi)
        ctx.fill()
        if label:
            ctx.font = "12px sans-serif"
            ctx.fillStyle = "#14202f"
            ctx.textAlign = "left"
            ctx.fillText(label, self.sx(x) + 7, self.sy(y) - 7)

    def band(self, upper, lower, color):
        ctx = self.ctx
        ctx.fillStyle = color
        ctx.beginPath()
        for i, (x, y) in enumerate(upper):
            if i == 0:
                ctx.moveTo(self.sx(x), self.sy(y))
            else:
                ctx.lineTo(self.sx(x), self.sy(y))
        for x, y in reversed(lower):
            ctx.lineTo(self.sx(x), self.sy(y))
        ctx.closePath()
        ctx.fill()

    def note(self, text):
        self.ctx.font = "13px sans-serif"
        self.ctx.fillStyle = "#5a687a"
        self.ctx.textAlign = "center"
        self.ctx.fillText(text, WIDTH / 2, HEIGHT / 2)


def table(headers, rows):
    head = html.TR([html.TH(h) for h in headers])
    body = [html.TR([html.TD(cell) for cell in row]) for row in rows]
    return html.TABLE([head] + body)


# ---------------------------------------------------------------- 1. polynomial roots


def run_roots(ev=None):
    box = document["roots_result"]
    try:
        coeffs = nm.poly_trim(nm.parse_numbers(document["roots_coeffs"].value))
        roots = nm.poly_roots(coeffs)
    except ValueError as exc:
        show_error(box, str(exc))
        return
    box.clear()
    box <= html.DIV("p(x) = " + nm.poly_text(coeffs), Class="big")
    rows = []
    for i, root in enumerate(roots):
        rows.append([str(i + 1), nm.root_text(root), "{:.2e}".format(abs(nm.poly_eval(coeffs, root)))])
    box <= table(["#", "root", "|p(root)|"], rows)

    reach = max([1.0] + [abs(r.real) for r in roots] + [abs(r.imag) for r in roots]) * 1.35
    half_h = max(reach, max([1.0] + [abs(r.real) for r in roots]) * 1.35 * HEIGHT / WIDTH)
    half_w = half_h * WIDTH / HEIGHT
    plot = Plot("roots_plot", -half_w, half_w, -half_h, half_h)
    plot.axes()
    plot.ctx.font = "12px sans-serif"
    plot.ctx.fillStyle = "#5a687a"
    plot.ctx.textAlign = "left"
    plot.ctx.fillText("complex plane: Re horizontally, Im vertically", plot.left + 8, plot.top + 16)
    for root in roots:
        plot.dot(root.real, root.imag, "#0055a5", 5, nm.root_text(root))


# ---------------------------------------------------------------- 2. linear regression


def run_regression(ev=None):
    box = document["reg_result"]
    try:
        xs, ys = nm.parse_points(document["reg_data"].value)
        model = nm.linear_regression(xs, ys)
        steps = int(float(document["reg_steps"].value or 0))
        extra = document["reg_x"].value.strip()
        future = nm.forecast(model, xs, steps)
        if extra:
            future.append((float(extra), nm.predict(model, float(extra))))
    except ValueError as exc:
        show_error(box, str(exc))
        return
    sign = "+" if model["intercept"] >= 0 else "−"
    box.clear()
    box <= html.DIV("y = %s·x %s %s" % (fmt(model["slope"]), sign, fmt(abs(model["intercept"]))), Class="big")
    box <= html.DIV("R² = %s    RMSE = %s    n = %d" % (fmt(model["r2"]), fmt(model["rmse"]), model["n"]))
    rows = []
    for x, y in future:
        low, high = nm.prediction_band(model, x)
        rows.append([fmt(x), fmt(y), "%s … %s" % (fmt(low), fmt(high))])
    if rows:
        box <= table(["x", "forecast", "95 % band"], rows)

    all_x = xs + [x for x, _ in future]
    all_y = ys + [v for x, y in future for v in nm.prediction_band(model, x)] + [nm.predict(model, x) for x in (min(all_x), max(all_x))]
    pad_x = (max(all_x) - min(all_x)) * 0.05 or 1
    pad_y = (max(all_y) - min(all_y)) * 0.08 or 1
    x0, x1 = min(all_x) - pad_x, max(all_x) + pad_x
    plot = Plot("reg_plot", x0, x1, min(all_y) - pad_y, max(all_y) + pad_y)
    plot.axes()
    if future and model["sigma"] > 0:
        steps_x = [x0 + (x1 - x0) * k / 60 for k in range(61)]
        first = min(x for x, _ in future)
        grid = [x for x in steps_x if x >= first] or [first]
        upper = [(x, nm.prediction_band(model, x)[1]) for x in grid]
        lower = [(x, nm.prediction_band(model, x)[0]) for x in grid]
        plot.band(upper, lower, "rgba(230, 126, 34, 0.18)")
    plot.line([(x0, nm.predict(model, x0)), (x1, nm.predict(model, x1))], "#0055a5")
    for x, y in zip(xs, ys):
        plot.dot(x, y, "#14202f", 4)
    for x, y in future:
        plot.dot(x, y, "#e67e22", 5)


# ---------------------------------------------------------------- 3. optimum


def heat_colour(t):
    """0 (low) ... 1 (high) -> from deep blue to a pale tone."""
    r = int(18 + 222 * t)
    g = int(60 + 175 * t)
    b = int(130 + 110 * t)
    return "rgb(%d,%d,%d)" % (r, g, b)


def plot_optimum(expression, start, result, maximize, bracket):
    dimension = len(start)
    best = result["x"]
    path = result["path"]
    f = nm.compile_function(expression, dimension)
    sign = -1.0 if maximize else 1.0
    if dimension == 1:
        if result["method"] == "golden":
            lo, hi = bracket
        else:
            points = [p[0] for p in path] + [best[0]]
            span = max(max(points) - min(points), 2.0)
            lo, hi = min(points) - span * 0.6, max(points) + span * 0.6
        curve = [(lo + (hi - lo) * k / 240, 0.0) for k in range(241)]
        curve = [(x, f([x])) for x, _ in curve]
        values = [y for _, y in curve]
        pad = (max(values) - min(values)) * 0.08 or 1
        plot = Plot("opt_plot", lo, hi, min(values) - pad, max(values) + pad)
        plot.axes()
        plot.line(curve, "#0055a5")
        for p in path[::max(1, len(path) // 40)]:
            plot.dot(p[0], f(p), "#e67e22", 3)
        plot.dot(start[0], f(start), "#2e9e5b", 5, "start")
        plot.dot(best[0], result["fx"], "#c0392b", 6, "%s" % result["kind"])
    elif dimension == 2:
        pts = path + [best, start]
        cx, cy = best[0], best[1]
        half = max(max(abs(p[0] - cx) for p in pts), max(abs(p[1] - cy) for p in pts) * WIDTH / HEIGHT, 1.0) * 1.3
        xmin, xmax = cx - half, cx + half
        half_y = half * HEIGHT / WIDTH
        ymin, ymax = cy - half_y, cy + half_y
        plot = Plot("opt_plot", xmin, xmax, ymin, ymax)
        cols, rows = 64, 42
        grid = []
        for j in range(rows):
            row = []
            for i in range(cols):
                gx = xmin + (xmax - xmin) * (i + 0.5) / cols
                gy = ymin + (ymax - ymin) * (j + 0.5) / rows
                row.append(sign * f([gx, gy]))
            grid.append(row)
        flat = [v for row in grid for v in row]
        low = min(flat)
        span = math.log(1 + (max(flat) - low)) or 1.0
        cell_w = (WIDTH - plot.left - plot.right) / cols
        cell_h = (HEIGHT - plot.top - plot.bottom) / rows
        for j in range(rows):
            for i in range(cols):
                t = math.log(1 + (grid[j][i] - low)) / span
                plot.ctx.fillStyle = heat_colour(t)
                plot.ctx.fillRect(plot.left + i * cell_w, HEIGHT - plot.bottom - (j + 1) * cell_h, cell_w + 1, cell_h + 1)
        plot.axes()
        plot.line([(p[0], p[1]) for p in path[::max(1, len(path) // 300)]] + [(best[0], best[1])], "#e67e22", 2)
        plot.dot(start[0], start[1], "#2e9e5b", 5, "start")
        plot.dot(best[0], best[1], "#c0392b", 6, result["kind"])
    else:
        plot = Plot("opt_plot", 0, 1, 0, 1)
        plot.note("three variables: the plot is skipped, see the numbers")


def run_optimum(ev=None):
    box = document["opt_result"]
    try:
        expression = document["opt_func"].value
        start = nm.parse_numbers(document["opt_start"].value)
        method = document["opt_method"].value
        maximize = document["opt_max"].checked
        bracket = nm.parse_numbers(document["opt_bracket"].value)
        bracket = bracket if len(bracket) == 2 else None
        result = nm.minimize(expression, start, method, maximize, bracket)
        plot_optimum(expression, start, result, maximize, bracket)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError) as exc:
        show_error(box, str(exc))
        return
    box.clear()
    names = nm.VARIABLES[:len(start)]
    where = ", ".join("%s = %s" % (n, fmt(v)) for n, v in zip(names, result["x"]))
    box <= html.DIV("%s at %s" % (result["kind"], where), Class="big")
    state = "converged" if result["converged"] else "stopped at the iteration limit"
    box <= table(
        ["f at the point", "method", "iterations", "state"],
        [[fmt(result["fx"]), result["method"], str(result["iterations"]), state]],
    )


def pick_example(ev):
    func, start, method, maximize = document["opt_example"].value.split("|")
    document["opt_func"].value = func
    document["opt_start"].value = start
    document["opt_method"].value = method
    document["opt_max"].checked = maximize == "1"
    run_optimum()


def pick_polynomial(ev):
    document["roots_coeffs"].value = document["roots_example"].value
    run_roots()


# ---------------------------------------------------------------- start


def start():
    document["roots_coeffs"].value = ", ".join("{:g}".format(c) for c in nm.DEMO_POLYNOMIALS[0])
    document["reg_data"].value = nm.DEMO_SERIES
    document["opt_bracket"].value = "-2, 2"
    pick = document["opt_example"]
    func, point, method, maximize = pick.value.split("|")
    document["opt_func"].value = func
    document["opt_start"].value = point

    for name in TABS:
        document["tab_" + name].bind("click", lambda ev, n=name: show_tab(n))
    document["roots_run"].bind("click", run_roots)
    document["reg_run"].bind("click", run_regression)
    document["opt_run"].bind("click", run_optimum)
    document["roots_example"].bind("change", pick_polynomial)
    document["opt_example"].bind("change", pick_example)

    run_roots()
    run_regression()
    run_optimum()

    query = window.location.search
    if "tab=" in query:
        show_tab(query.split("tab=")[1].split("&")[0])
    version = "Brython %s.%s.%s" % tuple(sys.implementation.version[:3])
    document["status"].text = version + " · numerics.py is shared with the CPython tests"
    if "autorun=1" in query:
        # the machine-readable copy of everything computed in the browser, read by the test
        document["dump"].text = json.dumps(nm.demo_report())
        document["status"].text += " · autorun done"


start()
