from __future__ import annotations

import json
import os
import socket
import unittest
import urllib.request

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
