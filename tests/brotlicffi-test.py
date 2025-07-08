import brotlicffi
import unittest

class TestBrotliCFFI(unittest.TestCase):
    def setUp(self):
        self.sample_data = b"Hello, this is a test string to compress with brotlicffi."
    
    def test_compress_and_decompress(self):
        compressed = brotlicffi.compress(self.sample_data)
        self.assertIsInstance(compressed, bytes)
        self.assertLess(len(compressed), len(self.sample_data))

        decompressed = brotlicffi.decompress(compressed)
        self.assertEqual(decompressed, self.sample_data)

    def test_compression_with_options(self):
        compressed = brotlicffi.compress(self.sample_data, quality=9, mode=brotlicffi.MODE_TEXT)
        self.assertIsInstance(compressed, bytes)
        self.assertTrue(len(compressed) > 0)

        decompressed = brotlicffi.decompress(compressed)
        self.assertEqual(decompressed, self.sample_data)

    def test_invalid_decompression(self):
        with self.assertRaises(brotlicffi.error):
            brotlicffi.decompress(b"This is not brotli compressed data")

if __name__ == '__main__':
    unittest.main()