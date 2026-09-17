from __future__ import annotations

import socket
import unittest

from configs.cfg import SAMPLES_DIR
from lab1.client import send_student
from lab1.codecs import attach_photo, dumps_json, dumps_pickle, loads_json_student, loads_pickle
from lab1.models import Student
from lab1.net import pack_envelope, recv_message, send_message, unpack_envelope
from lab1.server import StudentServer
from lab2.rpc_client import call
from lab2.rpc_server import RpcServer
from lab4.bridge_server import MethodBridge, send_request
from lab4.dynamic_student import Student as DynStudent
from lab4.dynamic_student import make_student
from lab4.inspector import describe
from lab4.runtime_methods import run_annotated_tests


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


class Lab2RpcTests(unittest.TestCase):
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


class Lab4ReflectionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
