"""Checkable JSP scenarios: the war, the handout prototype, rates, an image, the translator and the site."""

from __future__ import annotations

import html
import http.cookiejar
import io
import re
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime

from PIL import Image

from lab5 import runtime
from lab5.runtime import Tomcat

_TOMCAT: Tomcat | None = None


def ensure_server() -> Tomcat:
    global _TOMCAT
    if _TOMCAT is None or not _TOMCAT.running:
        _TOMCAT = Tomcat()
        _TOMCAT.start()
    return _TOMCAT


def stop_server() -> None:
    global _TOMCAT
    if _TOMCAT is not None:
        _TOMCAT.stop()
        _TOMCAT = None


def _browser() -> urllib.request.OpenerDirector:
    """A client with cookies, so the session (and the session beans) survive between requests."""
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch(path: str, opener: urllib.request.OpenerDirector | None = None, **params: str) -> tuple[str, str]:
    """(Content-Type, body) of a page of the web application."""
    query = "?" + urllib.parse.urlencode(params) if params else ""
    with (opener or _browser()).open(ensure_server().page(path, query), timeout=20) as response:
        return response.headers["Content-Type"], response.read().decode("utf-8")


def text(body: str) -> str:
    """The visible text of a page: tags removed, entities decoded, spaces collapsed."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def _span(body: str, element_id: str) -> str:
    found = re.search(rf'id="{element_id}">([^<]*)<', body)
    if not found:
        raise AssertionError(f"#{element_id} not on the page: {text(body)[:300]}")
    return found.group(1).strip()


# ---------------------------------------------------------------- cases


def environment() -> str:
    java, home = runtime.require()
    server = ensure_server()
    _type, body = fetch("index.jsp")
    found = re.search(r"Apache Tomcat (\S+), Java (\S+)\.", text(body))
    if not found:
        raise AssertionError(text(body)[:300])
    return f"Tomcat {found.group(1)} on Java {found.group(2)} at {server.url} ({home.name})"


def war_build() -> str:
    war = runtime.build_war()
    with zipfile.ZipFile(war) as archive:
        names = set(archive.namelist())
    expected = {
        "index.jsp", "hello.jsp", "response.jsp", "currency.jsp", "rate.jsp", "ImageServlet.jsp", "image.html",
        "translate.jsp", "site.jsp", "WEB-INF/web.xml", "WEB-INF/classes/com/Hello.class",
        "WEB-INF/classes/com/CurrencyBean.class", "WEB-INF/classes/com/Dictionary.class",
    }
    missing = expected - names
    if missing:
        raise AssertionError(f"not in {war.name}: {sorted(missing)}")
    jsp = sum(name.endswith(".jsp") for name in names)
    return f"{war.name}: {jsp} JSP pages, 3 beans in WEB-INF/classes ({war.stat().st_size // 1024} KiB)"


def today_page() -> str:
    content_type, body = fetch("index.jsp")
    found = re.search(r"TODAY IS: (\d\d\.\d\d\.\d{4} \d\d:\d\d:\d\d)", text(body))
    if "Hello from JSP" not in body or not found or "text/html" not in content_type:
        raise AssertionError(text(body)[:300])
    shown = datetime.strptime(found.group(1), "%d.%m.%Y %H:%M:%S")
    if abs((shown - datetime.now()).total_seconds()) > 120:
        raise AssertionError(f"the server time {shown} is far from the local clock")
    return f"<%! String getDate() %> + <%= getDate() %> -> TODAY IS: {found.group(1)}"


def hello_prototype() -> str:
    browser = _browser()
    _type, form = fetch("hello.jsp", browser)
    if 'action="response.jsp"' not in form:
        raise AssertionError("no form posting to response.jsp")
    _type, first = fetch("response.jsp", browser, name="Oleg")
    _type, again = fetch("response.jsp", browser)  # no parameter: jsp:setProperty keeps the session value
    if "Hello, Oleg!" not in text(first) or "Hello, Oleg!" not in text(again):
        raise AssertionError((text(first)[:200], text(again)[:200]))
    return "form -> response.jsp?name=Oleg -> Hello, Oleg!; the session bean keeps the name"


def _rate(browser: urllib.request.OpenerDirector, name: str | None = None) -> tuple[str, float, str, str]:
    _type, body = fetch("rate.jsp", browser, **({"name": name} if name is not None else {}))
    found = re.search(r"1 (USD|EUR) = ([0-9.]+) BYN", text(body))
    if not found:
        raise AssertionError(f"no rate for {name!r}: {text(body)[:300]}")
    day = re.search(r"Date (\d{4}-\d\d-\d\d)", text(body))
    return found.group(1), float(found.group(2)), _span(body, "source"), day.group(1) if day else ""


def currency_rates() -> str:
    browser = _browser()
    answers = {name: _rate(browser, name) for name in ("dollar", "USD", "доллар", "euro", "EUR", "Евро")}
    for name, (code, rate, source, day) in answers.items():
        expected = "USD" if name.lower() in ("dollar", "usd", "доллар") else "EUR"
        if code != expected:
            raise AssertionError(f"{name} -> {code}")
        if not 1.5 < rate < 6 or source not in ("NBRB", "table"):
            raise AssertionError(f"{name}: {rate} from {source}")
    usd, eur = answers["dollar"], answers["euro"]
    if eur[1] <= usd[1]:
        raise AssertionError(f"EUR {eur[1]} is not above USD {usd[1]}")
    if usd[2] == "NBRB" and date.fromisoformat(usd[3]) < date.today().replace(day=1):
        raise AssertionError(f"the National Bank rate is old: {usd[3]}")
    same = _rate(browser)  # rate.jsp without a parameter: the session bean still holds the last currency
    if same[0] != "EUR":
        raise AssertionError(f"session bean lost the currency: {same}")
    _type, unknown = fetch("rate.jsp", browser, name="yen")
    if "Unknown currency" not in text(unknown):
        raise AssertionError(text(unknown)[:300])
    return f"USD {usd[1]:.4f}, EUR {eur[1]:.4f} BYN ({usd[2]}, {usd[3]}); 6 spellings, session bean, unknown 'yen' refused"


def image_png() -> str:
    _type, page = fetch("image.html")
    if '<img id="picture" class="generated" src="ImageServlet.jsp"' not in page:
        raise AssertionError("image.html does not load ImageServlet.jsp")
    with urllib.request.urlopen(ensure_server().page("ImageServlet.jsp", "?text=Lab%205&w=400&h=240"), timeout=20) as response:
        content_type, payload = response.headers["Content-Type"], response.read()
    if content_type != "image/png" or payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{content_type}, {payload[:8]!r}")
    picture = Image.open(io.BytesIO(payload)).convert("RGB")
    if picture.size != (400, 240):
        raise AssertionError(picture.size)
    if picture.getpixel((5, 5)) != (0, 0, 255):
        raise AssertionError(f"background {picture.getpixel((5, 5))}")
    sun = picture.getpixel((400 - 2 * 30, 2 * 30))  # r = min(w, h) / 8 = 30, centre (w - 2r, 2r)
    if sun != (255, 255, 0):
        raise AssertionError(f"sun {sun}")
    letters = picture.crop((40, 90, 300, 125))  # the text baseline is at h / 2
    white = sum(1 for pixel in letters.getdata() if min(pixel) > 230)
    if white < 300:
        raise AssertionError(f"only {white} white pixels where the text should be")
    return f"image/png {picture.size[0]}x{picture.size[1]}, {len(payload)} bytes: blue background, yellow sun, {white} white text pixels"


def translator() -> str:
    pairs = {"cat": "кот", "Hello": "привет", "  THANK   you ": "спасибо", "собака": "dog", "Книга": "book", "зеленый": "green"}
    for word, expected in pairs.items():
        _type, body = fetch("translate.jsp", word=word)
        if _span(body, "translation") != expected:
            raise AssertionError(f"{word!r} -> {_span(body, 'translation')!r}, expected {expected!r}")
        direction = "RU → EN" if re.search("[а-яё]", word.lower()) else "EN → RU"
        if _span(body, "direction") != direction:
            raise AssertionError(f"{word!r}: direction {_span(body, 'direction')}")
    _type, unknown = fetch("translate.jsp", word="<b>quark</b>")
    if 'id="unknown"' not in unknown or "<b>quark" in unknown:
        raise AssertionError("an unknown word must be reported and escaped")
    size = re.search(r"Lexicon \((\d+) words\)", text(unknown))
    return f"{len(pairs)} words in both directions, case and spaces ignored; lexicon of {size.group(1) if size else '?'} words"


def site_writer() -> str:
    pages = {"home": "Welcome", "labs": "Labs of the course", "tomcat": "Server", "about": "About"}
    for page, heading in pages.items():
        content_type, body = fetch("site.jsp", page=page)
        if "charset=utf-8" not in content_type.lower() or not body.lstrip().startswith("<!DOCTYPE html>"):
            raise AssertionError(f"{page}: {content_type}, starts with {body[:30]!r}")
        if f'id="page-{page}"' not in body or f"<h2>{heading}</h2>" not in body or 'class="on"' not in body:
            raise AssertionError(f"{page}: {text(body)[:300]}")
    _type, labs = fetch("site.jsp", page="labs")
    rows = labs.count("<tr><td>")
    _type, fallback = fetch("site.jsp", page="../../etc/passwd")
    if 'id="page-home"' not in fallback:
        raise AssertionError("an unknown page must fall back to home")
    return f"{len(pages)} pages written by PrintWriter ot = response.getWriter(), {rows} labs in the table"
