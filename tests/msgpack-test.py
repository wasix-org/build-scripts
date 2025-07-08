import unittest
import msgpack


class TestMsgpackBasicFunctions(unittest.TestCase):

    def test_pack_unpack_integer(self):
        data = 42
        packed = msgpack.packb(data)
        unpacked = msgpack.unpackb(packed)
        self.assertEqual(data, unpacked)

    def test_pack_unpack_string(self):
        data = "hello msgpack"
        packed = msgpack.packb(data, use_bin_type=True)
        unpacked = msgpack.unpackb(packed, raw=False)
        self.assertEqual(data, unpacked)

    def test_pack_unpack_list(self):
        data = [1, 2, 3, "four"]
        packed = msgpack.packb(data, use_bin_type=True)
        unpacked = msgpack.unpackb(packed, raw=False)
        self.assertEqual(data, unpacked)

    def test_pack_unpack_dict(self):
        data = {"key": "value", "num": 123}
        packed = msgpack.packb(data, use_bin_type=True)
        unpacked = msgpack.unpackb(packed, raw=False)
        self.assertEqual(data, unpacked)

    def test_pack_unpack_nested(self):
        data = {"list": [1, {"nested": "dict"}], "bool": True}
        packed = msgpack.packb(data, use_bin_type=True)
        unpacked = msgpack.unpackb(packed, raw=False)
        self.assertEqual(data, unpacked)


if __name__ == '__main__':
    unittest.main()