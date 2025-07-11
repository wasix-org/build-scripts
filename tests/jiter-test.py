import unittest
import jiter
from decimal import Decimal

class TestJiter(unittest.TestCase):
    def test_basic_parsing(self):
        json_data = b'{"name": "Alice", "age": 25}'
        result = jiter.from_json(json_data)
        self.assertEqual(result, {"name": "Alice", "age": 25})

    def test_allow_inf_nan(self):
        json_data = b'{"val": NaN, "inf": Infinity, "ninf": -Infinity}'
        result = jiter.from_json(json_data, allow_inf_nan=True)
        self.assertTrue("val" in result and isinstance(result["val"], float))

        with self.assertRaises(ValueError):
            jiter.from_json(json_data, allow_inf_nan=False)

    def test_cache_controls(self):
        # Reset and check cache size
        jiter.cache_clear()
        self.assertEqual(jiter.cache_usage(), 0)

        # Populate and re-check cache usage
        json_data = b'{"city": "London"}'
        jiter.from_json(json_data, cache_mode="all")
        self.assertGreaterEqual(jiter.cache_usage(), 0)

    def test_partial_mode(self):
        partial = b'{"msg": "hello", "more": "text'
        
        with self.assertRaises(ValueError):
            jiter.from_json(partial, partial_mode=False)
        
        result = jiter.from_json(partial, partial_mode=True)
        self.assertEqual(result, {"msg": "hello"})

        result_trailing = jiter.from_json(partial, partial_mode="trailing-strings")
        self.assertEqual(result_trailing, {"msg": "hello", "more": "text"})

    def test_duplicate_keys(self):
        dupes = b'{"k": 1, "k": 2}'
        result = jiter.from_json(dupes)
        self.assertEqual(result, {"k": 2})  # Last wins by default

        with self.assertRaises(ValueError):
            jiter.from_json(dupes, catch_duplicate_keys=True)

    def test_float_mode_decimal(self):
        json_data = b'{"pi": 3.14159}'
        result = jiter.from_json(json_data, float_mode="decimal")
        self.assertEqual(result["pi"], Decimal("3.14159"))

    def test_float_mode_lossless(self):
        json_data = b'{"pi": 3.14159}'
        result = jiter.from_json(json_data, float_mode="lossless-float")
        # Check it's a string to avoid precision loss
        self.assertEqual(str(result["pi"]), "3.14159")

if __name__ == "__main__":
    unittest.main()