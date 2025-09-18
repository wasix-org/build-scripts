# test_protobuf_basic.py

import unittest
from person_pb2 import Person


class TestProtobufBasic(unittest.TestCase):

    def setUp(self):
        self.person = Person(name="Alice", id=123, email="alice@example.com")

    def test_field_access(self):
        self.assertEqual(self.person.name, "Alice")
        self.assertEqual(self.person.id, 123)
        self.assertEqual(self.person.email, "alice@example.com")

    def test_serialization(self):
        serialized = self.person.SerializeToString()
        self.assertIsInstance(serialized, bytes)
        self.assertGreater(len(serialized), 0)

    def test_deserialization(self):
        serialized = self.person.SerializeToString()
        person_copy = Person()
        person_copy.ParseFromString(serialized)
        self.assertEqual(person_copy.name, "Alice")
        self.assertEqual(person_copy.id, 123)
        self.assertEqual(person_copy.email, "alice@example.com")

    def test_clear_field(self):
        self.person.ClearField("email")
        self.assertEqual(self.person.email, "")

    def test_unknown_field_ignored(self):
        # Protocol Buffers ignore unknown fields during deserialization.
        serialized = self.person.SerializeToString()
        corrupted = serialized + b"\x20\x01"  # Append unknown field (field number 4, varint 1)
        new_person = Person()
        new_person.ParseFromString(corrupted)
        self.assertEqual(new_person.name, "Alice")

    def test_default_values(self):
        empty_person = Person()
        self.assertEqual(empty_person.name, "")
        self.assertEqual(empty_person.id, 0)
        self.assertEqual(empty_person.email, "")

    def test_repr_str(self):
        repr_str = str(self.person)
        self.assertIn("Alice", repr_str)
        self.assertIn("id: 123", repr_str)


if __name__ == '__main__':
    unittest.main()