# Lab 3: Brython

## Idea

A browser runs JavaScript only. **Brython** is a JavaScript program (`brython.js`) that reads `<script type="text/python">` blocks, translates the Python source to JavaScript in the page and runs it. The Python code gets the DOM through the `browser` package, so a client site can be written in Python instead of JavaScript.

## Terms

| Term | Meaning |
| --- | --- |
| `brython.js` | the compiler and runtime, loaded by a `<script src>` tag |
| `brython_stdlib.js` | the Python standard library packed for the browser |
| `brython()` | the function that finds and runs the Python scripts; called from `<body onload>` |
| `browser.document` | the DOM document; `document["id"]` is an element, `elt.bind("click", f)` adds a handler |
| `browser.html` | tag constructors: `html.H2("text")`, `html.TABLE(...)`; `document <= elt` appends |
| `pythonpath` | where `import` looks for your own `.py` modules (loaded by XHR) |

## The handout examples

1. `browser.html.H2(...)` and `document <= txt` create a heading from Python.
2. `<input id="div1">` + `<button id="bn">`: the handler `fun(ev)` reads `document["div1"].value` and calls `alert`.
3. A second and a third button: greeting and square (`float(...) ** 2`, `ValueError` → message).
4. The integral of `x**2` by the trapezoidal rule, result written into `output.text`.

Local files (`brython.js`, `brython_stdlib.js`) are used instead of the CDN, as the handout recommends: `pip install brython` puts them in `brython/data/`, and `scripts/fetch_runtimes.py` copies them to `lab3/site/`.

## The task

| Page | Method |
| --- | --- |
| Roots of a polynomial | Durand–Kerner iteration for all complex roots, polished by Newton steps; exact formulas for degrees 1 and 2; trailing zero coefficients give zero roots |
| Forecast by linear regression | least squares `y = a·x + b`, R², RMSE, forecast of the next steps with an approximate 95 % band |
| Optimum without restrictions | Nelder–Mead simplex, gradient descent with Armijo line search, golden section for one variable; the function is typed as text |

All three live in `lab3/numerics.py`, which imports only `math` and `cmath`. The same file is served to the browser (`/numerics.py`, imported with `pythonpath: ['/']`) and imported by the CPython tests, so the test compares what Brython computed in a real browser with what CPython computes.

## Things that differ from the handout (Brython 3.9 → 3.15)

- `import browser` no longer exposes `browser.html`; write `import browser.html` or `from browser import html`.
- Brython caches the stdlib in IndexedDB. A headless browser that dumps the DOM right after `load` sees an unfinished page; `brython({indexedDB: false})` makes the run synchronous.
- `"%g" % x` and `"%e" % x` are wrong for very small and very large numbers (`2.2e-16` prints as `0e+00`); `"{:g}".format(x)` is correct, so the page uses `str.format`.
- numpy and the other compiled packages are not available; numerical code must be pure Python.

## Links

- **Lab 2** put a method call behind a name in a registry; Brython puts a Python program behind a `<script>` tag. In both the client does not import the implementation.
- **Lab 4 (Jython)** is the mirror image: Python on the JVM instead of Python in the browser.
