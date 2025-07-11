import unittest
import io
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol
import qrcode


class TestPyzbarQRBuffer(unittest.TestCase):

    def setUp(self):
        # Generate QR code and save to an in-memory buffer
        self.test_data = "https://example.com"
        qr = qrcode.make(self.test_data)
        self.buffer = io.BytesIO()
        qr.save(self.buffer, format="PNG")
        self.buffer.seek(0)

    def test_qr_code_decoding(self):
        image = Image.open(self.buffer)
        decoded = decode(image, symbols=[ZBarSymbol.QRCODE])
        self.assertGreater(len(decoded), 0, "No QR code detected.")
        decoded_data = decoded[0].data.decode("utf-8")
        self.assertEqual(decoded_data, self.test_data, "Decoded data does not match original.")

    def tearDown(self):
        self.buffer.close()


if __name__ == "__main__":
    unittest.main()