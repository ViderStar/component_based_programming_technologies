"""Numerical methods for the Brython page: polynomial roots, linear regression, unconstrained optimum.

The module imports nothing but `math` and `cmath`, so the same file is imported by the page in the
browser (Brython) and by the tests in CPython. Annotations are kept out of the signatures on purpose:
Brython compiles this file in the browser and the fewer features it needs the faster the page loads.
"""

import cmath
import math

# ---------------------------------------------------------------- input


def parse_numbers(text):
    """'1, -6; 11 -6' -> [1.0, -6.0, 11.0, -6.0]. Separators: space, comma, semicolon, newline."""
    cleaned = text.replace(";", " ").replace(",", " ").replace("\n", " ").replace("\t", " ")
    values = []
    for token in cleaned.split():
        try:
            values.append(float(token))
        except ValueError:
            raise ValueError("not a number: " + token)
    return values


def parse_points(text):
    """Lines 'x y' (separators: space, comma, semicolon, tab) -> ([x...], [y...]).

    A single number per line is a value of the series y(1), y(2), ...
    """
    xs, ys = [], []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        numbers = parse_numbers(line)
        if len(numbers) == 1:
            xs.append(float(len(xs) + 1))
            ys.append(numbers[0])
        elif len(numbers) == 2:
            xs.append(numbers[0])
            ys.append(numbers[1])
        else:
            raise ValueError("a line must hold one or two numbers: " + line)
    return xs, ys


# ---------------------------------------------------------------- polynomial roots


def poly_trim(coeffs):
    """Drop leading zeros (coefficients are listed from the highest degree)."""
    coeffs = [c for c in coeffs]
    while coeffs and coeffs[0] == 0:
        coeffs.pop(0)
    return coeffs


def poly_eval(coeffs, x):
    """Horner scheme; works for real and complex x."""
    result = 0
    for c in coeffs:
        result = result * x + c
    return result


def poly_derivative(coeffs):
    degree = len(coeffs) - 1
    return [c * (degree - i) for i, c in enumerate(coeffs[:-1])]


def poly_text(coeffs):
    """[1, -6, 11, -6] -> 'x^3 - 6x^2 + 11x - 6'."""
    coeffs = poly_trim(coeffs)
    if not coeffs:
        return "0"
    degree = len(coeffs) - 1
    parts = []
    for i, c in enumerate(coeffs):
        power = degree - i
        if c == 0:
            continue
        magnitude = abs(c)
        number = "{:g}".format(magnitude)
        if power > 0 and magnitude == 1:
            number = ""
        term = number
        if power >= 1:
            term += "x"
        if power > 1:
            term += "^" + str(power)
        sign = "-" if c < 0 else "+"
        parts.append((sign, term))
    text = ("-" if parts[0][0] == "-" else "") + parts[0][1]
    for sign, term in parts[1:]:
        text += " " + sign + " " + term
    return text


def _cauchy_bound(coeffs):
    lead = abs(coeffs[0])
    return 1 + max(abs(c) for c in coeffs[1:]) / lead


def _clean(root):
    """Remove numerical dust: 2.0000000000001-1e-15j -> 2.0."""
    root = complex(root)
    scale = max(1.0, abs(root))
    real, imag = root.real, root.imag
    if abs(imag) < 1e-9 * scale:
        return complex(real, 0.0)
    if abs(real) < 1e-9 * scale:
        return complex(0.0, imag)
    return complex(real, imag)


def poly_roots(coeffs, tol=1e-14, max_iter=1000):
    """All complex roots of c[0]*x^n + ... + c[n] (Durand-Kerner, polished by Newton).

    Trailing zero coefficients give exact zero roots; degrees 1 and 2 use closed formulas.
    Returns the roots sorted by (real part, imaginary part).
    """
    coeffs = poly_trim([float(c) for c in coeffs])
    if len(coeffs) < 2:
        raise ValueError("a polynomial of degree 1 or higher is needed")
    roots = []
    while coeffs[-1] == 0:  # x divides the polynomial
        roots.append(complex(0.0, 0.0))
        coeffs.pop()
    degree = len(coeffs) - 1
    if degree == 1:
        roots.append(complex(-coeffs[1] / coeffs[0], 0.0))
    elif degree == 2:
        a, b, c = coeffs
        disc = cmath.sqrt(b * b - 4 * a * c)
        # the stable form avoids cancellation when b*b >> 4ac
        q = -0.5 * (b + (disc if b >= 0 else -disc))
        if q == 0:
            roots.extend([complex(0.0, 0.0), complex(0.0, 0.0)])
        else:
            roots.extend([complex(q / a), complex(c / q)])
    elif degree > 2:
        monic = [c / coeffs[0] for c in coeffs]
        radius = _cauchy_bound(monic)
        # starting points on a circle, rotated so that none lies on an axis of symmetry
        guess = [radius * 0.5 * cmath.exp(2j * math.pi * k / degree + 0.4j) for k in range(degree)]
        for _ in range(max_iter):
            largest = 0.0
            for i in range(degree):
                denominator = 1
                for j in range(degree):
                    if i != j:
                        denominator *= guess[i] - guess[j]
                if denominator == 0:
                    denominator = 1e-12
                step = poly_eval(monic, guess[i]) / denominator
                guess[i] -= step
                largest = max(largest, abs(step))
            if largest < tol:
                break
        derivative = poly_derivative(monic)
        for i in range(degree):  # Newton polishing against the original polynomial
            z = guess[i]
            for _ in range(5):
                slope = poly_eval(derivative, z)
                if slope == 0:
                    break
                z -= poly_eval(monic, z) / slope
            guess[i] = z
        roots.extend(guess)
    cleaned = [_clean(r) for r in roots]
    cleaned.sort(key=lambda r: (round(r.real, 9), round(r.imag, 9)))
    return cleaned


def root_text(root):
    """complex -> '2', '-1.5', '1 + 2i', '-i'. `str.format` is used: Brython's `%g` is unreliable."""
    real, imag = root.real, root.imag
    if imag == 0:
        return "{:.10g}".format(real + 0.0)
    if real == 0:
        if abs(imag) == 1:
            return "-i" if imag < 0 else "i"
        return "{:.10g}i".format(imag)
    sign = "-" if imag < 0 else "+"
    part = "{:.10g}".format(abs(imag))
    return "{:.10g} {} {}i".format(real, sign, "" if part == "1" else part)


# ---------------------------------------------------------------- linear regression


def linear_regression(xs, ys):
    """Least squares line y = slope*x + intercept; returns a dict with the model and its quality."""
    n = len(xs)
    if n != len(ys):
        raise ValueError("x and y must have the same length")
    if n < 2:
        raise ValueError("at least two points are needed")
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("all x values are equal: the slope is undefined")
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    residual = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    total = sum((y - mean_y) ** 2 for y in ys)
    r2 = 1.0 if total == 0 else 1 - residual / total
    rmse = math.sqrt(residual / n)
    # standard error of a new observation at x0: s * sqrt(1 + 1/n + (x0-mean)^2/sxx)
    sigma = math.sqrt(residual / (n - 2)) if n > 2 else 0.0
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "rmse": rmse,
        "sigma": sigma,
        "n": n,
        "mean_x": mean_x,
        "sxx": sxx,
    }


def predict(model, x):
    return model["slope"] * x + model["intercept"]


def prediction_band(model, x, z=1.96):
    """Approximate 95 % band for a new observation at x (normal quantile, not Student's)."""
    spread = z * model["sigma"] * math.sqrt(1 + 1 / model["n"] + (x - model["mean_x"]) ** 2 / model["sxx"])
    return predict(model, x) - spread, predict(model, x) + spread


def forecast(model, xs, steps):
    """Continue the series: the step is the mean spacing of x, the points follow the last x."""
    if len(xs) > 1:
        step = (xs[-1] - xs[0]) / (len(xs) - 1)
    else:
        step = 1.0
    future = [xs[-1] + step * (k + 1) for k in range(int(steps))]
    return [(x, predict(model, x)) for x in future]


# ---------------------------------------------------------------- unconstrained optimum

_SAFE = {
    "pi": math.pi,
    "e": math.e,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "atan": math.atan,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
    "pow": pow,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
}
VARIABLES = ("x", "y", "z")


def _identifiers(source):
    """Names used in an expression; letters that belong to a number (1e-3, 2E5) are not names."""
    names = []
    i = 0
    while i < len(source):
        ch = source[i]
        if ch.isalpha() or ch == "_":
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == "_"):
                j += 1
            word = source[i:j]
            exponent = i > 0 and (source[i - 1].isdigit() or source[i - 1] == ".") and word[0] in "eE"
            if not exponent:
                names.append(word)
            i = j
        elif ch.isdigit() or ch == ".":
            j = i
            while j < len(source) and (source[j].isdigit() or source[j] in ".eE" or
                                       (source[j] in "+-" and source[j - 1] in "eE")):
                j += 1
            i = j
        else:
            i += 1
    return names


def compile_function(expression, dimension):
    """'(1-x)^2 + 100*(y-x^2)^2' -> f(point). `^` means power; only math names are visible.

    The text is compiled once into a lambda, so the optimizer calls a plain function, not eval.
    """
    source = expression.strip().replace("^", "**")
    if not source:
        raise ValueError("the function is empty")
    names = VARIABLES[:dimension]
    for name in _identifiers(source):
        if name not in _SAFE and name not in names:
            raise ValueError("unknown name: " + name)
    scope = dict(_SAFE)
    scope["__builtins__"] = {}
    try:
        func = eval("lambda " + ", ".join(names) + ": (" + source + ")", scope)
    except SyntaxError:
        raise ValueError("cannot read the function: " + expression)

    def f(point):
        return float(func(*point))

    return f


def gradient(f, point, h=1e-6):
    """Central differences."""
    grad = []
    for i in range(len(point)):
        up = list(point)
        down = list(point)
        step = h * max(1.0, abs(point[i]))
        up[i] += step
        down[i] -= step
        grad.append((f(up) - f(down)) / (2 * step))
    return grad


def golden_section(f, a, b, tol=1e-9, max_iter=200):
    """Minimum of a unimodal f on [a, b]; f takes a one-element list like the other methods."""
    ratio = (math.sqrt(5) - 1) / 2
    c = b - ratio * (b - a)
    d = a + ratio * (b - a)
    fc, fd = f([c]), f([d])
    path = [[(a + b) / 2]]
    iterations = 0
    while abs(b - a) > tol and iterations < max_iter:
        iterations += 1
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            fc = f([c])
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            fd = f([d])
        path.append([(a + b) / 2])
    x = (a + b) / 2
    return {"x": [x], "fx": f([x]), "iterations": iterations, "converged": abs(b - a) <= tol, "path": path}


def gradient_descent(f, start, tol=1e-8, max_iter=20000):
    """Steepest descent with a backtracking (Armijo) line search and numerical gradient."""
    x = list(start)
    fx = f(x)
    path = [list(x)]
    step = 1.0
    for iteration in range(1, max_iter + 1):
        grad = gradient(f, x)
        norm = math.sqrt(sum(g * g for g in grad))
        if norm < tol:
            return {"x": x, "fx": fx, "iterations": iteration - 1, "converged": True, "path": path}
        step = min(step * 2, 1e3)
        while True:
            trial = [xi - step * gi for xi, gi in zip(x, grad)]
            ftrial = f(trial)
            if ftrial <= fx - 1e-4 * step * norm * norm:
                break
            step /= 2
            if step < 1e-16:
                return {"x": x, "fx": fx, "iterations": iteration, "converged": norm < 1e-5, "path": path}
        x, fx = trial, ftrial
        path.append(list(x))
    return {"x": x, "fx": fx, "iterations": max_iter, "converged": False, "path": path}


def nelder_mead(f, start, tol=1e-12, max_iter=4000, scale=0.5):
    """Derivative-free simplex search; copes with the narrow valley of the Rosenbrock function."""
    n = len(start)
    simplex = [list(start)]
    for i in range(n):
        vertex = list(start)
        vertex[i] += scale if vertex[i] == 0 else scale * abs(vertex[i]) + 0.05
        simplex.append(vertex)
    values = [f(v) for v in simplex]
    path = [list(start)]
    iteration = 0
    while iteration < max_iter:
        order = sorted(range(n + 1), key=lambda k: values[k])
        simplex = [simplex[k] for k in order]
        values = [values[k] for k in order]
        path.append(list(simplex[0]))
        spread = max(abs(values[k] - values[0]) for k in range(1, n + 1))
        size = max(max(abs(simplex[k][i] - simplex[0][i]) for i in range(n)) for k in range(1, n + 1))
        if spread < tol and size < 1e-8:
            break
        iteration += 1
        centroid = [sum(simplex[k][i] for k in range(n)) / n for i in range(n)]
        worst = simplex[n]
        reflected = [c + (c - w) for c, w in zip(centroid, worst)]
        fr = f(reflected)
        if values[0] <= fr < values[n - 1]:
            simplex[n], values[n] = reflected, fr
        elif fr < values[0]:
            expanded = [c + 2 * (c - w) for c, w in zip(centroid, worst)]
            fe = f(expanded)
            if fe < fr:
                simplex[n], values[n] = expanded, fe
            else:
                simplex[n], values[n] = reflected, fr
        else:
            if fr < values[n]:
                contracted = [c + 0.5 * (r - c) for c, r in zip(centroid, reflected)]
            else:
                contracted = [c + 0.5 * (w - c) for c, w in zip(centroid, worst)]
            fc = f(contracted)
            if fc < min(fr, values[n]):
                simplex[n], values[n] = contracted, fc
            else:  # shrink towards the best vertex
                best = simplex[0]
                for k in range(1, n + 1):
                    simplex[k] = [b + 0.5 * (v - b) for b, v in zip(best, simplex[k])]
                    values[k] = f(simplex[k])
    best = min(range(n + 1), key=lambda k: values[k])
    return {
        "x": simplex[best],
        "fx": values[best],
        "iterations": iteration,
        "converged": iteration < max_iter,
        "path": path,
    }


METHODS = ("nelder-mead", "gradient", "golden")


def minimize(expression, start, method="nelder-mead", maximize=False, bracket=None):
    """Optimum of the function typed by the user; maximization minimizes -f.

    `start` fixes the dimension (1 to 3 variables). The golden-section method needs a bracket (a, b)
    and works for one variable only. The reported value `fx` is the value of the original function.
    """
    dimension = len(start)
    if not 1 <= dimension <= len(VARIABLES):
        raise ValueError("1 to 3 variables are supported")
    base = compile_function(expression, dimension)
    sign = -1.0 if maximize else 1.0

    def target(point):
        value = sign * base(point)
        if value != value:
            raise ValueError("the function is not a number at " + str(point))
        return value

    if method == "golden":
        if dimension != 1:
            raise ValueError("golden section works for one variable")
        a, b = bracket if bracket else (start[0] - 10, start[0] + 10)
        result = golden_section(target, a, b)
    elif method == "gradient":
        result = gradient_descent(target, start)
    elif method == "nelder-mead":
        result = nelder_mead(target, start)
    else:
        raise ValueError("unknown method: " + method)
    result["fx"] = sign * result["fx"]
    result["method"] = method
    result["kind"] = "maximum" if maximize else "minimum"
    return result


# ---------------------------------------------------------------- demo data shared by the page and the tests

DEMO_POLYNOMIALS = [
    [1, -6, 11, -6],
    [1, 0, 1],
    [1, 0, 0, 0, -1],
    [1, -10, 35, -50, 24],
    [2, 0, -8, 0, 0],
]
DEMO_SERIES = "1 102\n2 108\n3 113\n4 121\n5 124\n6 133\n7 137\n8 146\n9 149\n10 158"
DEMO_FUNCTIONS = [
    # expression, start point, method, maximize, bracket
    ("(x - 1)^2 + 2*(y + 2)^2 + x*y", [0.0, 0.0], "nelder-mead", False, None),
    ("(x - 1)^2 + 2*(y + 2)^2 + x*y", [0.0, 0.0], "gradient", False, None),
    ("(1 - x)^2 + 100*(y - x^2)^2", [-1.2, 1.0], "nelder-mead", False, None),
    ("x^4 - 3*x^2 + x", [2.0], "gradient", False, None),
    ("x^4 - 3*x^2 + x", [0.0], "golden", False, [-0.5, 2.0]),
    ("sin(x)*exp(-0.1*x)", [1.0], "nelder-mead", True, None),
]


def demo_report():
    """Everything the page computes on its own examples, as plain lists and numbers (JSON-ready)."""
    report = {"polynomials": [], "regression": None, "optima": []}
    for coeffs in DEMO_POLYNOMIALS:
        roots = poly_roots(coeffs)
        report["polynomials"].append(
            {
                "text": poly_text(coeffs),
                "roots": [[r.real, r.imag] for r in roots],
                "residual": max(abs(poly_eval([float(c) for c in coeffs], r)) for r in roots),
            }
        )
    xs, ys = parse_points(DEMO_SERIES)
    model = linear_regression(xs, ys)
    report["regression"] = {
        "slope": model["slope"],
        "intercept": model["intercept"],
        "r2": model["r2"],
        "forecast": [[x, y] for x, y in forecast(model, xs, 4)],
    }
    for expression, start, method, maximize, bracket in DEMO_FUNCTIONS:
        result = minimize(expression, start, method, maximize, bracket)
        report["optima"].append(
            {
                "function": expression,
                "method": method,
                "kind": result["kind"],
                "x": result["x"],
                "fx": result["fx"],
                "converged": result["converged"],
            }
        )
    return report
