# Not tested on native
# Broken on WASIX
import unittest
import os
import tempfile
from tokenizers import Tokenizer
from tokenizers import BertWordPieceTokenizer, ByteLevelBPETokenizer

class TestTokenizersBasic(unittest.TestCase):
    def test_load_pretrained_and_encode(self):
        tokenizer = Tokenizer.from_pretrained("bert-base-cased")
        encoded = tokenizer.encode("Hello World!")
        self.assertIsInstance(encoded.ids, list)
        self.assertIsInstance(encoded.tokens, list)
        self.assertGreater(len(encoded.ids), 0)

    def test_wordpiece_tokenizer(self):
        tokenizer = BertWordPieceTokenizer()
        text = "Tokenizers are fast!"
        encoding = tokenizer.encode(text)
        self.assertIn("Tokenizers", encoding.tokens)
        self.assertEqual(" ".join(encoding.tokens), "Tokenizers are fast!")

    def test_bytelevel_bpe_encode_decode(self):
        tokenizer = ByteLevelBPETokenizer()
        # Train a very tiny tokenizer inline
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("hello\nworld\n")
            fname = f.name
        tokenizer.train([fname], vocab_size=50, min_frequency=1)
        os.unlink(fname)

        text = "hello world"
        encoding = tokenizer.encode(text)
        decoded = tokenizer.decode(encoding.ids)
        self.assertEqual(decoded.strip(), text)

    def test_offsets(self):
        tokenizer = BertWordPieceTokenizer()
        encoding = tokenizer.encode("Hello world")
        # Ensure each token has an offset tuple
        for offset in encoding.offsets:
            self.assertIsInstance(offset, tuple)
            self.assertEqual(len(offset), 2)

    def test_truncation_and_padding(self):
        tokenizer = BertWordPieceTokenizer()
        tokenizer.enable_truncation(max_length=5)
        tokenizer.enable_padding(length=5)

        text = "This is a long text that will be truncated"
        encoding = tokenizer.encode(text)
        self.assertEqual(len(encoding.ids), 5)

    def test_save_and_reload(self):
        tokenizer = BertWordPieceTokenizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "tokenizer.json")
            tokenizer.save(file_path)
            self.assertTrue(os.path.exists(file_path))
            # Load back
            tokenizer2 = Tokenizer.from_file(file_path)
            encoding = tokenizer2.encode("hello world")
            self.assertGreater(len(encoding.ids), 0)

if __name__ == "__main__":
    unittest.main()