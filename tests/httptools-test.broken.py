import unittest

try:
    import httptools
    from httptools import (
        HttpRequestParser,
        HttpResponseParser,
        parse_url,
        HttpParserUpgrade,
    )
except Exception:
    # Make import errors explicit when running the suite
    raise


class RecorderProtocol:
    """Protocol object that records callbacks and data for assertions."""

    def __init__(self):
        self.events = []
        self.url = b""
        self.status = b""
        self.headers = []  # list[(name, value)] in arrival order
        self.body = b""

    # --- common callbacks ---
    def on_message_begin(self):
        self.events.append("message_begin")

    def on_url(self, url: bytes):
        self.events.append("url")
        self.url += url

    def on_header(self, name: bytes, value: bytes):
        self.events.append("header")
        self.headers.append((name, value))

    def on_headers_complete(self):
        self.events.append("headers_complete")

    def on_body(self, body: bytes):
        self.events.append("body")
        self.body += body

    def on_message_complete(self):
        self.events.append("message_complete")

    def on_chunk_header(self):
        self.events.append("chunk_header")

    def on_chunk_complete(self):
        self.events.append("chunk_complete")

    def on_status(self, status: bytes):
        self.events.append("status")
        self.status += status


class MinimalProtocol:
    """Protocol with only one callback to verify optionality of others."""

    def __init__(self):
        self.completed = False

    def on_message_complete(self):
        self.completed = True


class MultiRecorderProtocol(RecorderProtocol):
    """
    Recorder that snapshots per-message data when on_message_complete fires.
    Useful to verify pipelining behavior.
    """

    def __init__(self):
        super().__init__()
        self.messages = []

    def on_message_complete(self):
        # snapshot and reset per-message fields we care about
        self.messages.append(
            {"url": self.url, "headers": list(self.headers), "body": self.body}
        )
        self.url = b""
        self.headers.clear()
        self.body = b""
        self.events.append("message_complete")


class HttpRequestParserTests(unittest.TestCase):
    def make_parser(self, proto=None):
        return HttpRequestParser(proto or RecorderProtocol())

    def test_parse_simple_get(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        data = (
            b"GET /hello?name=world HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"User-Agent: test\r\n"
            b"\r\n"
        )
        parser.feed_data(data)

        self.assertIn("message_begin", proto.events)
        self.assertIn("headers_complete", proto.events)
        self.assertIn("message_complete", proto.events)
        self.assertEqual(parser.get_http_version(), "1.1")
        self.assertTrue(parser.should_keep_alive())  # HTTP/1.1 default keep-alive
        self.assertEqual(parser.get_method(), b"GET")
        self.assertEqual(proto.url, b"/hello?name=world")
        # ensure header order preserved
        self.assertEqual(
            proto.headers, [(b"Host", b"example.com"), (b"User-Agent", b"test")]
        )

    def test_parse_with_body_and_connection_close(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        body = b"abc123" * 3
        data = (
            b"POST /submit HTTP/1.0\r\n"
            b"Host: a\r\n"
            b"Connection: close\r\n"
            b"Content-Length: %d\r\n\r\n" % len(body)
        ) + body
        parser.feed_data(data)

        self.assertEqual(parser.get_http_version(), "1.0")
        self.assertFalse(parser.should_keep_alive())  # explicit close
        self.assertEqual(proto.body, body)
        self.assertIn((b"Content-Length", str(len(body)).encode()), proto.headers)

    def test_incremental_feed_splits(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        request = (
            b"PUT /x HTTP/1.1\r\n"
            b"Host: h\r\nContent-Length: 4\r\n\r\n"
            b"DEAD"
        )
        # Feed in odd boundaries to exercise internal buffering
        for chunk in [request[:5], request[5:17], request[17:28], request[28:]]:
            parser.feed_data(chunk)
        self.assertEqual(proto.body, b"DEAD")
        self.assertIn("message_complete", proto.events)

    def test_chunked_body_events(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        data = (
            b"POST /chunks HTTP/1.1\r\n"
            b"Host: e\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n"
            b"4\r\nWiki\r\n"
            b"5\r\npedia\r\n"
            b"0\r\n\r\n"
        )
        parser.feed_data(data)
        # order and presence of chunk callbacks
        self.assertIn("chunk_header", proto.events)
        self.assertIn("chunk_complete", proto.events)
        self.assertEqual(proto.body, b"Wikipedia")
        self.assertIn("message_complete", proto.events)

    def test_should_upgrade_flag_and_exception(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        pre = (
            b"GET / HTTP/1.1\r\n"
            b"Host: a\r\n"
            b"Connection: Upgrade\r\n"
            b"Upgrade: websocket\r\n\r\n"
        )
        tail = b"NONHTTP"  # bytes belonging to the upgraded protocol
        data = pre + tail
        with self.assertRaises(HttpParserUpgrade) as ctx:
            parser.feed_data(data)
        # should_upgrade is set just before on_headers_complete
        self.assertTrue(parser.should_upgrade())
        # The exception contains the offset of the non-HTTP bytes within `data`
        self.assertEqual(ctx.exception.args[0], len(pre))

    def test_missing_callbacks_are_optional(self):
        proto = MinimalProtocol()
        parser = HttpRequestParser(proto)
        parser.feed_data(b"HEAD / HTTP/1.1\r\nHost: a\r\n\r\n")
        self.assertTrue(proto.completed)

    # --- New & fixed coverage ---

    def test_head_no_body(self):
        """HEAD without payload bytes -> no body callbacks."""
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        data = (
            b"HEAD /resource HTTP/1.1\r\n"
            b"Host: example\r\n"
            b"\r\n"
        )
        parser.feed_data(data)
        self.assertNotIn("body", proto.events)
        self.assertEqual(proto.body, b"")
        self.assertEqual(parser.get_method(), b"HEAD")

    def test_head_with_payload_bytes_is_forwarded(self):
        """If payload bytes are present, parser forwards them (semantics up to app)."""
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        data = (
            b"HEAD /resource HTTP/1.1\r\n"
            b"Host: example\r\n"
            b"Content-Length: 5\r\n"
            b"\r\n"
            b"XXXXX"
        )
        parser.feed_data(data)
        self.assertIn("body", proto.events)
        self.assertEqual(proto.body, b"XXXXX")

    def test_http10_keep_alive_header_overrides_default(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        parser.feed_data(
            b"GET / HTTP/1.0\r\n"
            b"Host: h\r\n"
            b"Connection: keep-alive\r\n\r\n"
        )
        self.assertTrue(parser.should_keep_alive())

    def test_http11_connection_close(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        parser.feed_data(
            b"GET / HTTP/1.1\r\n"
            b"Host: h\r\n"
            b"Connection: close\r\n\r\n"
        )
        self.assertFalse(parser.should_keep_alive())

    def test_duplicate_headers_preserved(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        parser.feed_data(
            b"GET / HTTP/1.1\r\n"
            b"Host: h\r\n"
            b"Set-Cookie: a=1\r\n"
            b"Set-Cookie: b=2\r\n"
            b"\r\n"
        )
        self.assertEqual(
            [(n, v) for (n, v) in proto.headers if n == b"Set-Cookie"],
            [(b"Set-Cookie", b"a=1"), (b"Set-Cookie", b"b=2")],
        )

    def test_url_fragmented_across_chunks(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        parts = [
            b"GET /long",
            b"/path/with?qu",
            b"ery=1 HTTP/1.1\r\nHost: h\r\n\r\n",
        ]
        for p in parts:
            parser.feed_data(p)
        self.assertEqual(proto.url, b"/long/path/with?query=1")
        # ensure we saw url callback at least twice
        self.assertGreaterEqual(proto.events.count("url"), 2)

    def test_pipelined_two_requests_single_buffer(self):
        proto = MultiRecorderProtocol()
        parser = HttpRequestParser(proto)
        buf = (
            b"GET /a HTTP/1.1\r\nHost: h\r\n\r\n"
            b"POST /b HTTP/1.1\r\nHost: h\r\nContent-Length: 3\r\n\r\nXYZ"
        )
        parser.feed_data(buf)
        self.assertEqual(len(proto.messages), 2)
        self.assertEqual(proto.messages[0]["url"], b"/a")
        self.assertEqual(proto.messages[0]["body"], b"")
        self.assertEqual(proto.messages[1]["url"], b"/b")
        self.assertEqual(proto.messages[1]["body"], b"XYZ")

    def test_body_streaming_many_small_chunks(self):
        proto = RecorderProtocol()
        parser = HttpRequestParser(proto)
        header = b"POST /s HTTP/1.1\r\nHost: h\r\nContent-Length: 10\r\n\r\n"
        body = b"abcdefghij"
        # feed headers, then body one byte at a time
        parser.feed_data(header)
        for b_ in body:
            parser.feed_data(bytes([b_]))
        self.assertEqual(proto.body, body)
        # on_body should have fired multiple times
        self.assertGreaterEqual(proto.events.count("body"), 5)


class HttpResponseParserTests(unittest.TestCase):
    def make_parser(self, proto=None):
        return HttpResponseParser(proto or RecorderProtocol())

    def test_parse_simple_200(self):
        proto = RecorderProtocol()
        parser = HttpResponseParser(proto)
        body = b"OK"
        data = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: %d\r\n\r\n" % len(body)
        ) + body
        parser.feed_data(data)
        self.assertIn("status", proto.events)
        # Reason phrase only (httptools passes reason to on_status)
        self.assertEqual(proto.status, b"OK")
        self.assertEqual(parser.get_status_code(), 200)
        self.assertEqual(parser.get_http_version(), "1.1")
        self.assertTrue(parser.should_keep_alive())
        self.assertEqual(proto.body, body)

    def test_response_connection_close(self):
        proto = RecorderProtocol()
        parser = HttpResponseParser(proto)
        data = (
            b"HTTP/1.0 204 No Content\r\n"
            b"Connection: close\r\n\r\n"
        )
        parser.feed_data(data)
        self.assertEqual(parser.get_status_code(), 204)
        self.assertEqual(parser.get_http_version(), "1.0")
        self.assertFalse(parser.should_keep_alive())

    def test_response_chunked(self):
        proto = RecorderProtocol()
        parser = HttpResponseParser(proto)
        data = (
            b"HTTP/1.1 200 OK\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n"
            b"3\r\nHel\r\n"
            b"2\r\nlo\r\n"
            b"0\r\n\r\n"
        )
        parser.feed_data(data)
        self.assertIn("chunk_header", proto.events)
        self.assertIn("chunk_complete", proto.events)
        self.assertEqual(proto.body, b"Hello")
        self.assertIn("message_complete", proto.events)

    def test_pipelined_two_responses_single_buffer(self):
        proto = MultiRecorderProtocol()
        parser = HttpResponseParser(proto)
        buf = (
            b"HTTP/1.1 204 No Content\r\n\r\n"
            b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nDATA"
        )
        parser.feed_data(buf)
        # We can't query both status codes here (parser holds the last),
        # but we can assert message boundaries & bodies.
        self.assertEqual(len(proto.messages), 2)
        self.assertEqual(proto.messages[0]["body"], b"")
        self.assertEqual(proto.messages[1]["body"], b"DATA")
        self.assertEqual(parser.get_status_code(), 200)  # last response


class ParseUrlTests(unittest.TestCase):
    def test_parse_full_url(self):
        url = parse_url(b"https://user:pass@example.com:8443/path/to?q=1#frag")
        self.assertEqual(url.schema, b"https")
        self.assertEqual(url.host, b"example.com")
        self.assertEqual(url.port, 8443)
        self.assertEqual(url.path, b"/path/to")
        self.assertEqual(url.query, b"q=1")
        self.assertEqual(url.fragment, b"frag")
        self.assertEqual(url.userinfo, b"user:pass")

    def test_parse_relative_path(self):
        url = parse_url(b"/just/a/path?x=y")
        self.assertIsNone(url.schema)
        self.assertIsNone(url.host)
        self.assertIsNone(url.port)
        self.assertEqual(url.path, b"/just/a/path")
        self.assertEqual(url.query, b"x=y")
        self.assertIsNone(url.fragment)
        self.assertIsNone(url.userinfo)

    def test_parse_host_without_port(self):
        url = parse_url(b"http://example.org/")
        self.assertEqual(url.schema, b"http")
        self.assertEqual(url.host, b"example.org")
        self.assertIsNone(url.port)
        self.assertEqual(url.path, b"/")

    def test_parse_url_ipv6_host_and_edge_cases(self):
        # IPv6 host with port
        u = parse_url(b"http://[2001:db8::1]:8080/a?x#y")
        self.assertEqual(u.schema, b"http")
        self.assertEqual(u.host, b"2001:db8::1")
        self.assertEqual(u.port, 8080)
        self.assertEqual(u.path, b"/a")
        self.assertEqual(u.query, b"x")
        self.assertEqual(u.fragment, b"y")

        # userinfo without password
        u2 = parse_url(b"https://alice@example.org/")
        self.assertEqual(u2.userinfo, b"alice")

        # only fragment
        u3 = parse_url(b"/path#frag")
        self.assertEqual(u3.path, b"/path")
        self.assertEqual(u3.fragment, b"frag")
        self.assertIsNone(u3.schema)
        self.assertIsNone(u3.host)

        # empty query may be normalized to b"" or None depending on implementation
        u4 = parse_url(b"/p?")
        self.assertEqual(u4.path, b"/p")
        self.assertTrue(u4.query in (b"", None))


if __name__ == "__main__":
    unittest.main()