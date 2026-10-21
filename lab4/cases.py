"""Checkable Jython scenarios: Java from Python, Python from Java, files, images and the menu application."""

from __future__ import annotations

import re
import time

from PIL import Image, ImageChops, ImageStat

from configs.cfg import SAMPLES_DIR
from lab4 import runtime
from lab4.runtime import WORK_DIR, run_jython

PICTURES = {
    "picture1": runtime.PROJECT_ROOT / "assets" / "lab4" / "picture1.jpg",
    "picture2": runtime.PROJECT_ROOT / "assets" / "lab4" / "picture2.png",
}
# geometry of the plot area in Canvas.sine_frame (menu_app.py): left, top, right margin, bottom margin
SINE_MARGINS = (56, 24, 24, 44)


def _snapshot(view: str, name: str, *extra: str, size: str = "640x400") -> tuple[Image.Image, str]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    target = WORK_DIR / name
    output = run_jython("menu_app.py", "--snapshot", str(target), "--view", view, "--size", size, *extra)
    with Image.open(target) as opened:
        return opened.convert("RGB"), output


def _blue(pixel: tuple[int, int, int]) -> bool:
    return abs(pixel[0] - 0) < 45 and abs(pixel[1] - 85) < 45 and abs(pixel[2] - 165) < 45


# ---------------------------------------------------------------- cases


def environment() -> str:
    java, jar = runtime.require()
    output = run_jython("java_version.py")
    version = re.search(r"Running on Java version: (\S+)", output)
    millis = re.search(r"Unix time from Java: (\d+)", output)
    jython = re.search(r"Jython version: (\S+)", output)
    if not (version and millis and jython):
        raise AssertionError(output)
    if abs(int(millis.group(1)) / 1000 - time.time()) > 120:
        raise AssertionError("System.currentTimeMillis() is far from the local clock")
    return f"Java {version.group(1)} + Jython {jython.group(1)} ({jar.name})"


def hello_world() -> str:
    lines = run_jython("hello_world.py").splitlines()
    if lines != ["Hello, world!", "Hello, Oleg!"]:
        raise AssertionError(lines)
    return "sys.stdout.write and print give the same result"


def files() -> str:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    target = WORK_DIR / "example_dir" / "example_file.txt"
    target.unlink(missing_ok=True)
    output = run_jython("files_demo.py", str(WORK_DIR))
    if "has been written" not in output or target.read_text() != "This is an example file.":
        raise AssertionError(output)
    return f"java.io.File and FileWriter created {target.name} ({target.stat().st_size} bytes)"


def python_class_extends_java() -> str:
    lines = run_jython("my_class.py").splitlines()
    if lines[0] != "Hello, world! Form Class" or "isinstance(z, Object): True" not in lines:
        raise AssertionError(lines)
    return "class MyClass(Object): a Python class is a Java object"


def java_collections() -> str:
    lines = run_jython("array_list.py").splitlines()
    if lines[:2] != ["Hello", "world"] or "size from Java: 2, len() from Python: 2" not in lines:
        raise AssertionError(lines)
    return "ArrayList is iterated with a Python for loop and has len()"


def jar_import() -> str:
    jar = runtime.build_jar()
    lines = run_jython("call_java_class.py", str(jar)).splitlines()
    if lines != ["Hello, dear oleg", "static call: Hello, dear Jython"]:
        raise AssertionError(lines)
    return f"sys.path.append({jar.name}); from com import MyClass -> {lines[0]}"


def java_calls_python() -> str:
    lines = runtime.run_java_embedding().splitlines()
    if lines != ["Hello Python World!", "Hello, John!", "Python computed n ** 2 = 100"]:
        raise AssertionError(lines)
    return "PythonInterpreter inside Java: exec, import of jy10, set/get of values"


def images_and_sound() -> str:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    drawn = WORK_DIR / "drawn.png"
    run_jython("draw_image.py", str(drawn))
    with Image.open(drawn) as opened:
        picture = opened.convert("RGB")
    if picture.size != (200, 200) or picture.getpixel((10, 10)) != (255, 255, 255) or picture.getpixel((50, 100)) != (255, 0, 0):
        raise AssertionError("Graphics2D drawing differs from the lecture")
    info = run_jython("image_viewer.py", str(PICTURES["picture1"]), "--info")
    if "480x320" not in info:
        raise AssertionError(info)
    sound = run_jython("music_player.py", str(SAMPLES_DIR / "sample.wav"), "--info")
    if "22050.0 Hz" not in sound:
        raise AssertionError(sound)
    return "BufferedImage rect and oval drawn, JPEG read by ImageIO (480x320), WAV opened by javax.sound"


def menu_items() -> str:
    output = run_jython("menu_app.py", "--selftest")
    for fragment in ("menus: File, Draw, Help", "-> mode picture, caption 'picture1.jpg'", "-> mode picture, caption 'picture2.png'", "-> mode sine", "-> mode empty", "selftest ok"):
        if fragment not in output:
            raise AssertionError(f"{fragment!r} not in\n{output}")
    return "Draw > Picture 1, Picture 2, Sine wave, Clear: the canvas follows every click"


def _check_picture(view: str) -> str:
    image, output = _snapshot(view, f"{view}.png")
    box = re.search(r"image box: (\d+) (\d+) (\d+) (\d+)", output)
    if not box:
        raise AssertionError(output)
    x, y, w, h = (int(v) for v in box.groups())
    drawn = image.crop((x, y, x + w, y + h))
    with Image.open(PICTURES[view]) as source:
        reference = source.convert("RGB").resize((w, h), Image.LANCZOS)
    difference = ImageStat.Stat(ImageChops.difference(drawn, reference)).mean
    if max(difference) > 6:
        raise AssertionError(f"the canvas differs from {PICTURES[view].name}: {difference}")
    return f"{PICTURES[view].name} drawn at {w}x{h}, mean error {max(difference):.1f}/255"


def menu_picture1() -> str:
    return _check_picture("picture1")


def menu_picture2() -> str:
    return _check_picture("picture2")


def menu_sine() -> str:
    image, _output = _snapshot("sine", "sine.png")
    width, height = image.size
    left, top = SINE_MARGINS[0], SINE_MARGINS[1]
    plot_w, plot_h = width - SINE_MARGINS[0] - SINE_MARGINS[2], height - SINE_MARGINS[1] - SINE_MARGINS[3]
    pixels = image.load()
    column_y: dict[int, float] = {}
    for x in range(left + 2, left + plot_w - 1):
        rows = [y for y in range(top + 1, top + plot_h) if _blue(pixels[x, y])]
        if rows:
            column_y[x] = sum(rows) / len(rows)
    if len(column_y) < plot_w * 0.95:
        raise AssertionError("the curve is not continuous")
    middle = top + plot_h / 2
    crossings = [
        x for x in sorted(column_y)[1:] if (column_y[x] - middle) * (column_y.get(x - 1, column_y[x]) - middle) < 0
    ]
    expected = [left + plot_w * k / 4 for k in (1, 2, 3)]  # sin(x) = 0 at pi, 2pi, 3pi of [0, 4pi]
    if len(crossings) != 3 or any(abs(a - b) > 3 for a, b in zip(crossings, expected)):
        raise AssertionError(f"zero crossings {crossings}, expected {expected}")
    top_x = min(column_y, key=lambda x: column_y[x])  # the first crest is at pi/2
    if abs(top_x - (left + plot_w / 8)) > 4:
        raise AssertionError(f"first crest at x={top_x}")
    amplitude = (middle - min(column_y.values())) / (plot_h / 2)
    if abs(amplitude - 1 / 1.2) > 0.03:
        raise AssertionError(f"amplitude {amplitude:.3f}")
    return f"zero crossings at {', '.join(str(c) for c in crossings)} px, crest at {top_x} px, amplitude {amplitude:.2f} of the half-height"


def menu_window() -> str:
    plain, _ = _snapshot("sine", "frame.png", "--frame")
    opened, _ = _snapshot("sine", "frame_popup.png", "--frame", "--popup", "Draw")
    if plain.size != opened.size or plain.size[1] <= 400:
        raise AssertionError((plain.size, opened.size))
    changed = ImageChops.difference(plain, opened).getbbox()
    if changed is None or changed[1] > 40:
        raise AssertionError("the open Draw menu is not in the picture")
    return f"window content {plain.size[0]}x{plain.size[1]} (menu bar, canvas, status line); the open menu changes {changed}"


def swing_window() -> str:
    """The JFrame of the handout: needs a screen, so it is the one case that is not headless."""
    if not runtime.display_available():
        return "skipped: no display"
    output = run_jython("greet_frame.py", "--selftest", headless=False, timeout=45)
    if "Hello, Oleg!" not in output or "field after Clear: ''" not in output:
        raise AssertionError(output)
    return "JFrame opened, Greet printed the name, Clear emptied the field"
