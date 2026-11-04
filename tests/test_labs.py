from __future__ import annotations

import json
import os
import socket
import unittest
import urllib.request
from pathlib import Path

from configs.cfg import SAMPLES_DIR
from lab1.client import send_student
from lab1.codecs import attach_photo, dumps_json, dumps_pickle, loads_json_student, loads_pickle
from lab1.models import Student
from lab1.net import pack_envelope, recv_message, send_message, unpack_envelope
from lab1.server import StudentServer
from lab2 import registry
from lab2.calculator import Calculator
from lab2.client import ComError, Dispatch
from lab2.web import WebServer
from lab3 import cases as lab3_cases
from lab3 import numerics
from lab3.server import SiteServer
from lab4 import cases as lab4_cases
from lab4 import runtime as jython_runtime
from lab5 import cases as lab5_cases
from lab5 import runtime as tomcat_runtime
from lab1.extras.rpc.rpc_client import call
from lab1.extras.rpc.rpc_server import RpcServer
from lab1.extras.reflection.bridge_server import MethodBridge, send_request
from lab1.extras.reflection.dynamic_student import Student as DynStudent
from lab1.extras.reflection.dynamic_student import make_student
from lab1.extras.reflection.inspector import describe
from lab1.extras.reflection.runtime_methods import run_annotated_tests


class Lab1CodecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.student = Student(name="Artem", group="m2", faculty="ITAS")
        photo = SAMPLES_DIR / "avatar.webp"
        if photo.exists():
            attach_photo(self.student, photo)
        else:
            self.student.photo = None

    def test_pickle_roundtrip(self) -> None:
        restored = loads_pickle(dumps_pickle(self.student))
        self.assertEqual(restored.name, self.student.name)
        if self.student.photo:
            self.assertEqual(restored.photo.data, self.student.photo.data)
            self.assertGreater(len(restored.photo.data), 1024)

    def test_json_base64_roundtrip(self) -> None:
        restored = loads_json_student(dumps_json(self.student))
        self.assertEqual(restored.faculty, "ITAS")
        if self.student.photo:
            self.assertEqual(restored.photo.mime, "image/webp")
            self.assertEqual(restored.photo.data, self.student.photo.data)


class Lab1NetworkTests(unittest.TestCase):
    def test_length_prefix_large_payload(self) -> None:
        payload = b"x" * 5000
        left, right = socket.socketpair()
        try:
            send_message(left, pack_envelope("json", payload))
            fmt, body = unpack_envelope(recv_message(right))
            self.assertEqual(fmt, "json")
            self.assertEqual(len(body), 5000)
        finally:
            left.close()
            right.close()

    def test_server_echo_json(self) -> None:
        student = Student(name="A", group="B", faculty="C")
        server = StudentServer(port=18003)
        server.start()
        try:
            echoed = send_student(student, fmt="json", port=18003)
            self.assertEqual(echoed.name, "A")
        finally:
            server.stop()


class ExtraRpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = RpcServer(port=18000)
        cls.server.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def test_add_mul(self) -> None:
        self.assertEqual(call("add", 2, 3, port=18000), 5)
        self.assertEqual(call("mul", 6, 7, port=18000), 42)

    def test_inspect(self) -> None:
        members = call("inspect_module", port=18000)
        self.assertIn("add", members)


class ExtraReflectionTests(unittest.TestCase):
    def test_dynamic_class_and_signature(self) -> None:
        person = make_student("Ivan", "1")
        self.assertIsInstance(person, DynStudent)
        names = {item.name: item for item in describe(person)}
        self.assertIn("greet", names)
        self.assertIn("()", names["greet"].signature)
        self.assertEqual(person.greet(), "Hello, from Ivan")

    def test_annotated_methods(self) -> None:
        lines = run_annotated_tests()
        self.assertTrue(any(line.startswith("PASS") for line in lines))
        self.assertEqual(len(lines), 2)

    def test_java_bridge_protocol(self) -> None:
        bridge = MethodBridge(port=18010)
        bridge.start()
        try:
            reply = send_request("greet", port=18010)
            self.assertTrue(reply["ok"])
            self.assertIn("Hello, from", reply["result"])
        finally:
            bridge.stop()


class Lab2ComTests(unittest.TestCase):
    def setUp(self) -> None:
        registry.register(Calculator)

    def test_dispatch_runs_in_another_process(self) -> None:
        calc = Dispatch("Lab2.Calculator")
        try:
            self.assertNotEqual(calc.pid, os.getpid())
            self.assertEqual(calc.Add(2, 3), 5)
            self.assertEqual(calc.Sub(7, 10), -3)
            self.assertEqual(calc.Mul(6, 7), 42)
            self.assertEqual(calc.Div(7, 2), 3.5)
            self.assertEqual(calc.Pow(2, 10), 1024)
        finally:
            calc.Release()

    def test_com_errors(self) -> None:
        calc = Dispatch("Lab2.Calculator")
        try:
            with self.assertRaises(ComError) as failed:
                calc.Div(1, 0)
            self.assertEqual(failed.exception.name, "DISP_E_EXCEPTION")
            with self.assertRaises(ComError) as hidden:
                calc.secret()
            self.assertEqual(hidden.exception.name, "DISP_E_UNKNOWNNAME")
            self.assertEqual(calc.Add(1, 1), 2)
        finally:
            calc.Release()

    def test_unregistered_progid(self) -> None:
        self.addCleanup(registry.register, Calculator)
        registry.unregister(Calculator)
        with self.assertRaises(ComError) as failed:
            Dispatch("Lab2.Calculator")
        self.assertEqual(failed.exception.name, "CO_E_CLASSSTRING")

    def test_html_endpoint(self) -> None:
        server = WebServer(port=18020)
        server.start()
        try:
            with urllib.request.urlopen(f"{server.url}calc?op=Mul&a=6&b=7", timeout=10) as response:
                self.assertEqual(json.loads(response.read())["result"], 42)
            with urllib.request.urlopen(f"{server.url}calc?op=Release&a=1&b=1", timeout=10) as response:
                self.assertIn("Unknown operation", json.loads(response.read())["error"])
        finally:
            server.stop()


class Lab3NumericsTests(unittest.TestCase):
    def test_polynomial_roots(self) -> None:
        roots = numerics.poly_roots([1, -6, 11, -6])
        self.assertEqual([round(r.real, 9) for r in roots], [1.0, 2.0, 3.0])
        self.assertTrue(all(r.imag == 0 for r in roots))

    def test_complex_pair_and_text(self) -> None:
        roots = numerics.poly_roots([1, 0, 1])
        self.assertEqual([numerics.root_text(r) for r in roots], ["-i", "i"])
        self.assertEqual(numerics.poly_text([1, -6, 11, -6]), "x^3 - 6x^2 + 11x - 6")

    def test_zero_roots_are_exact(self) -> None:
        self.assertEqual(sorted(r.real for r in numerics.poly_roots([2, 0, -8, 0, 0])), [-2.0, 0.0, 0.0, 2.0])

    def test_constant_has_no_roots(self) -> None:
        with self.assertRaises(ValueError):
            numerics.poly_roots([0, 0, 7])

    def test_regression_matches_statistics(self) -> None:
        import statistics

        xs, ys = numerics.parse_points(numerics.DEMO_SERIES)
        model = numerics.linear_regression(xs, ys)
        reference = statistics.linear_regression(xs, ys)
        self.assertAlmostEqual(model["slope"], reference.slope)
        self.assertAlmostEqual(model["intercept"], reference.intercept)
        self.assertAlmostEqual(numerics.forecast(model, xs, 1)[0][1], reference.slope * 11 + reference.intercept)

    def test_regression_needs_two_distinct_x(self) -> None:
        with self.assertRaises(ValueError):
            numerics.linear_regression([1, 1], [2, 3])

    def test_optimum_methods_agree(self) -> None:
        expression = "(x - 1)^2 + 2*(y + 2)^2 + x*y"
        expected = (16 / 7, -18 / 7)
        for method in ("nelder-mead", "gradient"):
            found = numerics.minimize(expression, [0.0, 0.0], method)["x"]
            self.assertAlmostEqual(found[0], expected[0], places=4, msg=method)
            self.assertAlmostEqual(found[1], expected[1], places=4, msg=method)

    def test_maximum_and_forbidden_names(self) -> None:
        top = numerics.minimize("-(x - 3)^2 + 5", [0.0], maximize=True)
        self.assertEqual(top["kind"], "maximum")
        self.assertAlmostEqual(top["fx"], 5.0, places=6)
        with self.assertRaises(ValueError):
            numerics.minimize("open('x')", [1.0])


class Lab3SiteTests(unittest.TestCase):
    def test_site_serves_shared_module(self) -> None:
        server = SiteServer(port=18030)
        server.start()
        try:
            for path in ("site/index.html", "site/app.py", "numerics.py"):
                with urllib.request.urlopen(f"http://{server.host}:{server.port}/{path}", timeout=10) as response:
                    self.assertEqual(response.status, 200)
            with urllib.request.urlopen(f"http://{server.host}:{server.port}/numerics.py", timeout=10) as response:
                served = response.read().decode("utf-8")
            self.assertEqual(served, Path(numerics.__file__).read_text(encoding="utf-8"))
        finally:
            server.stop()

    @unittest.skipIf(lab3_cases.find_browser() is None, "no Chromium-based browser")
    def test_brython_page_matches_cpython(self) -> None:
        try:
            self.assertIn("equal CPython", lab3_cases.brython_page())
        finally:
            lab3_cases.stop_server()


@unittest.skipUnless(jython_runtime.available(), "Java or the Jython jar is missing (python scripts/fetch_runtimes.py)")
class Lab4JythonTests(unittest.TestCase):
    def test_java_from_python(self) -> None:
        self.assertIn("Jython 2.7.3", lab4_cases.environment())
        self.assertIn("Hello, dear oleg", lab4_cases.jar_import())

    def test_python_from_java(self) -> None:
        self.assertIn("PythonInterpreter", lab4_cases.java_calls_python())

    def test_menu_application(self) -> None:
        self.assertIn("follows every click", lab4_cases.menu_items())
        self.assertIn("picture1.jpg", lab4_cases.menu_picture1())
        self.assertIn("picture2.png", lab4_cases.menu_picture2())
        self.assertIn("zero crossings", lab4_cases.menu_sine())
        self.assertIn("menu bar", lab4_cases.menu_window())


@unittest.skipUnless(tomcat_runtime.available(), "Java or Tomcat is missing (python scripts/fetch_runtimes.py)")
class Lab5JspTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        lab5_cases.stop_server()

    def test_war_and_server(self) -> None:
        self.assertIn("3 beans", lab5_cases.war_build())
        self.assertIn("Tomcat", lab5_cases.environment())
        self.assertIn("TODAY IS", lab5_cases.today_page())

    def test_beans(self) -> None:
        self.assertIn("Hello, Oleg!", lab5_cases.hello_prototype())
        self.assertIn("USD", lab5_cases.currency_rates())
        self.assertIn("both directions", lab5_cases.translator())

    def test_image_and_site(self) -> None:
        self.assertIn("image/png", lab5_cases.image_png())
        self.assertIn("response.getWriter()", lab5_cases.site_writer())


class LabCasesTests(unittest.TestCase):
    def test_lab1_file_cases(self) -> None:
        from lab1.cases import json_base64, pickle_file
        from lab1.runner import build_demo_student

        student = build_demo_student()
        self.assertIn("photo", pickle_file(student))
        self.assertIn("base64", json_base64(student))

    def test_reflection_case_greet(self) -> None:
        from lab1.extras.reflection.cases import annotated, dynamic_greet

        self.assertIn("Hello, from", dynamic_greet())
        self.assertTrue(annotated().endswith("PASS") or "PASS" in annotated())

    def test_lab2_cases(self) -> None:
        from lab2 import cases

        self.assertIn("LocalServer32", cases.registry_keys())
        self.assertIn("2^10=1024", cases.arithmetic())
        self.assertIn("CO_E_CLASSSTRING", cases.unregister())


if __name__ == "__main__":
    unittest.main()
