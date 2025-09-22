import io
import os
import struct
import tempfile
import unittest

# The tests assume the package name is `zstandard` (python-zstandard)
import zstandard as zstd


class TestZstandardModule(unittest.TestCase):
    SAMPLE_TEXT = (
        b"The quick brown fox jumps over the lazy dog. "
        b"Pack my box with five dozen liquor jugs.\n" * 50
    )

    def setUp(self):
        self.sample = self.SAMPLE_TEXT
        self.samples_list = [
            b"alpha " * 100,
            b"bravo " * 80,
            b"charlie " * 120,
            b"delta " * 60,
        ]

    # ---------- Basics & constants ----------

    def test_backend_and_basic_constants(self):
        self.assertIn(zstd.backend, ("cext", "cffi"))
        self.assertIsInstance(zstd.ZSTD_VERSION, tuple)
        self.assertGreaterEqual(zstd.MAX_COMPRESSION_LEVEL, 1)
        # Recommended sizes should be positive
        self.assertGreater(zstd.COMPRESSION_RECOMMENDED_INPUT_SIZE, 0)
        self.assertGreater(zstd.COMPRESSION_RECOMMENDED_OUTPUT_SIZE, 0)
        self.assertGreater(zstd.DECOMPRESSION_RECOMMENDED_INPUT_SIZE, 0)
        self.assertGreater(zstd.DECOMPRESSION_RECOMMENDED_OUTPUT_SIZE, 0)
        # Frame header/magic number types
        self.assertIsInstance(zstd.FRAME_HEADER, (bytes, bytearray, memoryview))
        self.assertIsInstance(zstd.MAGIC_NUMBER, int)

    # ---------- One-shot APIs ----------

    def test_one_shot_compress_decompress(self):
        for lvl in (-5, 1, 3, min(6, zstd.MAX_COMPRESSION_LEVEL)):
            with self.subTest(level=lvl):
                comp = zstd.compress(self.sample, level=lvl)
                self.assertIsInstance(comp, bytes)
                decomp = zstd.decompress(comp)
                self.assertEqual(decomp, self.sample)

    def test_one_shot_decompress_requires_max_output_if_unknown(self):
        # Build a stream without content size in header:
        cctx = zstd.ZstdCompressor(write_content_size=False)
        frame = cctx.compress(self.sample)
        # frame_content_size should be unknown (-1)
        cs = zstd.frame_content_size(frame)
        self.assertIn(cs, (-1, zstd.CONTENTSIZE_UNKNOWN))
        # ZstdDecompressor().decompress without max_output_size should fail.
        dctx = zstd.ZstdDecompressor()
        with self.assertRaises(zstd.ZstdError):
            dctx.decompress(frame)
        # Works with explicit max_output_size
        out = dctx.decompress(frame, max_output_size=len(self.sample))
        self.assertEqual(out, self.sample)

    # ---------- File API (zstandard.open) ----------

    def test_open_binary_and_text_modes(self):
        with tempfile.TemporaryDirectory() as td:
            bin_path = os.path.join(td, "bin.zst")
            txt_path = os.path.join(td, "text.zst")

            # Binary write/read
            with zstd.open(bin_path, mode="wb") as fh:
                fh.write(self.sample)
            with zstd.open(bin_path, mode="rb") as fh:
                data = fh.read()
            self.assertEqual(data, self.sample)

            # Text write/read
            text = "hello\nworld\n🙂\n" * 100
            with zstd.open(txt_path, mode="wt", encoding="utf-8") as fh:
                fh.write(text)
            with zstd.open(txt_path, mode="rt", encoding="utf-8") as fh:
                read_text = fh.read()
            self.assertEqual(text, read_text)

    # ---------- Streaming compression: writer/reader/copy_stream ----------

    def test_stream_writer_and_reader(self):
        raw = self.sample
        sink = io.BytesIO()
        cctx = zstd.ZstdCompressor(level=5)
        # Don't close the underlying sink so we can inspect it.
        with cctx.stream_writer(sink, write_size=32768, closefd=False) as w:
            for i in range(0, len(raw), 1234):
                w.write(raw[i : i + 1234])
            # finish frame explicitly to ensure full frame close
            w.flush(zstd.FLUSH_FRAME)
            self.assertGreaterEqual(w.tell(), 0)
            self.assertGreater(w.memory_size(), 0)

        comp = sink.getvalue()
        self.assertTrue(comp)

        # Decompress via stream_reader (pull)
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(io.BytesIO(comp)) as r:
            out = r.read()
            self.assertEqual(out, raw)
            self.assertFalse(r.readable() and r.writable())

    def test_copy_stream_roundtrip(self):
        cctx = zstd.ZstdCompressor()
        dctx = zstd.ZstdDecompressor()

        src = io.BytesIO(self.sample)
        comp = io.BytesIO()
        r, w = cctx.copy_stream(src, comp)
        self.assertGreater(r, 0)
        self.assertGreater(w, 0)

        comp.seek(0)
        out = io.BytesIO()
        r2, w2 = dctx.copy_stream(comp, out)
        self.assertGreater(r2, 0)
        self.assertGreater(w2, 0)
        self.assertEqual(out.getvalue(), self.sample)

    def test_read_to_iter_and_stream_reader_variants(self):
        cctx = zstd.ZstdCompressor()
        pieces = []
        for chunk in cctx.read_to_iter(io.BytesIO(self.sample), read_size=4096, write_size=8192):
            pieces.append(chunk)
        comp = b"".join(pieces)
        dctx = zstd.ZstdDecompressor()
        out = b"".join(dctx.read_to_iter(io.BytesIO(comp), read_size=2048, write_size=4096))
        self.assertEqual(out, self.sample)

    # ---------- compressobj / decompressobj ----------

    def test_standard_library_like_objects(self):
        cctx = zstd.ZstdCompressor()
        cobj = cctx.compressobj()
        part1 = cobj.compress(self.sample[:1000])
        part2 = cobj.compress(self.sample[1000:])
        final = cobj.flush()
        comp = part1 + part2 + final
        self.assertTrue(comp)

        # Decompress in chunks and test eof/unused_data/unconsumed_tail behavior
        dctx = zstd.ZstdDecompressor()
        dobj = dctx.decompressobj()
        out1 = dobj.decompress(comp[:50])
        out2 = dobj.decompress(comp[50:])
        out3 = dobj.flush()
        out = out1 + out2 + out3
        self.assertEqual(out, self.sample)
        self.assertTrue(dobj.eof)
        self.assertEqual(dobj.unconsumed_tail, b"")
        # Feed extra data after frame end
        dobj2 = dctx.decompressobj()
        dobj2.decompress(comp + b"EXTRA")
        self.assertNotEqual(dobj2.unused_data, b"")

    # ---------- chunker ----------

    def test_chunker_api(self):
        cctx = zstd.ZstdCompressor()
        chunker = cctx.chunker(chunk_size=32768)
        out_chunks = []
        # Feed in uneven piece sizes
        for i in range(0, len(self.sample), 777):
            for oc in chunker.compress(self.sample[i : i + 777]):
                out_chunks.append(oc)
        for oc in chunker.flush():
            out_chunks.append(oc)
        for oc in chunker.finish():
            out_chunks.append(oc)
        comp = b"".join(out_chunks)
        self.assertTrue(comp)
        # Use streaming decompression since content size may be unknown
        dctx = zstd.ZstdDecompressor()
        out = b"".join(dctx.read_to_iter(io.BytesIO(comp)))
        self.assertEqual(out, self.sample)

    # ---------- Decompression writer/reader wrappers ----------

    def test_decompression_wrappers(self):
        comp = zstd.compress(self.sample)
        # stream_writer (push). Keep sink open.
        dctx = zstd.ZstdDecompressor()
        sink = io.BytesIO()
        with dctx.stream_writer(sink, write_size=8192, closefd=False) as w:
            written = w.write(comp[:50])
            self.assertGreaterEqual(written, 0)
            written += w.write(comp[50:])
            w.flush()
            self.assertGreater(w.memory_size(), 0)
        self.assertEqual(sink.getvalue(), self.sample)

        # stream_reader again (pull) with seek/tell forward-only behavior
        with dctx.stream_reader(io.BytesIO(comp)) as r:
            self.assertEqual(r.tell(), 0)
            r.read(10_000)
            pos = r.tell()
            self.assertGreater(pos, 0)
            # seeking backwards should fail — some builds raise OSError, others ValueError
            with self.assertRaises((ValueError, OSError)):
                r.seek(0)

    # ---------- Dictionaries (train/use), dict chaining ----------

    def test_dictionary_train_and_use(self):
        # Use many varied small samples and a modest dict size to avoid "Src size is incorrect".
        varied_samples = [
            (f"sample-{i:04d}-" + "abcde"[i % 5] * (20 + (i % 13))).encode("ascii")
            for i in range(200)
        ]
        dict_candidate = zstd.train_dictionary(1024, varied_samples)
        # Some versions return bytes; wrap into ZstdCompressionDict if needed.
        if isinstance(dict_candidate, (bytes, bytearray, memoryview)):
            dict_obj = zstd.ZstdCompressionDict(dict_candidate)
        else:
            dict_obj = dict_candidate  # already a ZstdCompressionDict

        self.assertGreaterEqual(len(dict_obj), 0)
        dict_id = dict_obj.dict_id()
        self.assertIsInstance(dict_id, int)
        raw_dict = dict_obj.as_bytes()
        self.assertIsInstance(raw_dict, (bytes, bytearray))

        # Precompute for a specific level to speed up multi use
        dict_obj.precompute_compress(level=3)

        # Use dict for compression & decompression
        cctx = zstd.ZstdCompressor(dict_data=dict_obj)
        dctx = zstd.ZstdDecompressor(dict_data=dict_obj)
        frames = [cctx.compress(x) for x in self.samples_list]
        outs = []
        for fr in frames:
            buf = io.BytesIO()
            with dctx.stream_writer(buf, closefd=False) as dec:
                dec.write(fr)
            outs.append(buf.getvalue())
        self.assertEqual(outs, self.samples_list)

    def test_decompress_content_dict_chain(self):
        # Build a content-dictionary chain per docs
        inputs = [b"input 1", b"input 2", b"input 3"]
        frames = []
        frames.append(zstd.ZstdCompressor().compress(inputs[0]))
        for i, raw in enumerate(inputs[1:]):
            dict_data = zstd.ZstdCompressionDict(
                inputs[i], dict_type=zstd.DICT_TYPE_RAWCONTENT
            )
            frames.append(zstd.ZstdCompressor(dict_data=dict_data).compress(raw))
        # Should yield last input's raw bytes
        last = zstd.ZstdDecompressor().decompress_content_dict_chain(frames)
        self.assertEqual(last, inputs[-1])

    # ---------- Multi (de)compress to buffer (experimental) ----------

    def test_multi_ops_if_supported(self):
        # Skip if not supported in this installed version.
        have_multi_comp = hasattr(zstd.ZstdCompressor(), "multi_compress_to_buffer")
        have_multi_decomp = hasattr(zstd.ZstdDecompressor(), "multi_decompress_to_buffer")
        if zstd.backend == "cffi" or not (have_multi_comp and have_multi_decomp):
            self.skipTest("multi_* APIs not supported on this backend/version")

        cctx = zstd.ZstdCompressor()
        comp_collection = cctx.multi_compress_to_buffer(self.samples_list, threads=-1)
        self.assertGreater(len(comp_collection), 0)
        frames = [bytes(comp_collection[i]) for i in range(len(comp_collection))]

        dctx = zstd.ZstdDecompressor()
        sizes = struct.pack("=" + "Q" * len(self.samples_list), *[len(x) for x in self.samples_list])
        out_collection = dctx.multi_decompress_to_buffer(frames, decompressed_sizes=sizes, threads=-1)
        self.assertEqual(len(out_collection), len(self.samples_list))
        recon = [bytes(out_collection[i]) for i in range(len(out_collection))]
        self.assertEqual(recon, self.samples_list)

    # ---------- Frame inspection & utilities ----------

    def test_frame_header_and_parameters(self):
        cctx = zstd.ZstdCompressor(write_checksum=True, write_content_size=True)
        frame = cctx.compress(self.sample)
        # Header size should be parseable
        header_len = zstd.frame_header_size(frame)
        self.assertGreaterEqual(header_len, 4)
        # get_frame_parameters needs at least 18 bytes according to docs
        params = zstd.get_frame_parameters(frame[: max(18, header_len)])
        self.assertIsInstance(params, zstd.FrameParameters)
        self.assertTrue(params.has_checksum)
        # content size should be embedded
        self.assertEqual(params.content_size, len(self.sample))
        # frame_content_size should match
        self.assertEqual(zstd.frame_content_size(frame), len(self.sample))

    def test_estimate_context_sizes(self):
        self.assertGreater(zstd.estimate_decompression_context_size(), 0)
        params = zstd.ZstdCompressionParameters.from_level(4, source_size=len(self.sample))
        self.assertGreater(params.estimated_compression_context_size(), 0)
        # Override knobs
        params2 = zstd.ZstdCompressionParameters.from_level(
            3, window_log=10, threads=2, write_checksum=1
        )
        self.assertIsInstance(params2, zstd.ZstdCompressionParameters)

    # ---------- Progress & memory size ----------

    def test_frame_progression_and_memory_size(self):
        cctx = zstd.ZstdCompressor()
        _ = cctx.memory_size()
        ing, cons, prod = cctx.frame_progression()
        self.assertEqual(len((ing, cons, prod)), 3)
        # Do some streaming work and check progression changes
        sink = io.BytesIO()
        with cctx.stream_writer(sink, closefd=False) as w:
            w.write(self.sample[:1000])
            a = cctx.frame_progression()
            w.write(self.sample[1000:])
            b = cctx.frame_progression()
        self.assertNotEqual(a, b)

    # ---------- read_across_frames / allow_extra_data ----------

    def test_decompress_across_frames_and_extra_data(self):
        cctx = zstd.ZstdCompressor()
        frame1 = cctx.compress(b"A" * 10)
        frame2 = cctx.compress(b"B" * 20)
        combined_with_trailing = frame1 + frame2 + b"TRAILING"

        # ZstdDecompressor.decompress (single frame) should ignore extras by default
        dctx = zstd.ZstdDecompressor()
        data1 = dctx.decompress(combined_with_trailing)
        self.assertEqual(data1, b"A" * 10)

        # When allow_extra_data=False, extra should error
        with self.assertRaises(zstd.ZstdError):
            dctx.decompress(combined_with_trailing, allow_extra_data=False)

        # For read_across_frames=True, feed only valid frames (no trailing garbage).
        dctx2 = zstd.ZstdDecompressor()
        combined_frames_only = frame1 + frame2
        with dctx2.stream_reader(io.BytesIO(combined_frames_only), read_across_frames=True) as r:
            out = r.read()
        self.assertEqual(out, b"A" * 10 + b"B" * 20)

    # ---------- zstandard.open with user-provided contexts ----------

    def test_open_with_custom_contexts(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "ctx.zst")
            cctx = zstd.ZstdCompressor(level=7)
            with zstd.open(p, "wb", cctx=cctx) as fh:
                fh.write(self.sample)
            dctx = zstd.ZstdDecompressor()
            with zstd.open(p, "rb", dctx=dctx) as fh:
                self.assertEqual(fh.read(), self.sample)


if __name__ == "__main__":
    # Helpful hint when running locally: respect import policy via env var.
    # e.g. PYTHON_ZSTANDARD_IMPORT_POLICY=cext python test_zstandard.py
    print(f"Using python-zstandard backend: {zstd.backend}")
    unittest.main(verbosity=2)