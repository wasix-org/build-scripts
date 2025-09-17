#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import json
import socket
import tempfile
import time
from io import BytesIO

# PycURL is required for these tests.
try:
    import pycurl
except Exception as e:
    raise SystemExit("These tests require pycurl to be installed: %s" % e)

# certifi is optional but used for HTTPS where available
try:
    import certifi
    CAINFO_PATH = certifi.where()
except Exception:
    CAINFO_PATH = None

HTTPBIN = "http://httpbin.org"
HTTPBINS = "https://httpbin.org"


def has_network(host="httpbin.org", port=443, timeout=3.0):
    """Lightweight network check: DNS + TCP connect."""
    try:
        addr = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not addr:
            return False
        sock = socket.create_connection((addr[0][4][0], port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


NETWORK_AVAILABLE = has_network()


def network_required(test_func):
    """Decorator to skip tests that require network if not available."""
    reason = "Network to httpbin.org not available; skipping."
    return unittest.skipUnless(NETWORK_AVAILABLE, reason)(test_func)


def https_required(test_func):
    """Decorator to skip HTTPS tests if no CA bundle is available."""
    if not NETWORK_AVAILABLE:
        return unittest.skip("Network unavailable; skipping.")(test_func)
    if CAINFO_PATH is None:
        return unittest.skip("certifi not installed; skipping HTTPS tests.")(test_func)
    return test_func


def decode_body_to_json(body_bytes):
    try:
        return json.loads(body_bytes.decode("utf-8"))
    except Exception:
        # httpbin JSON should be utf-8; fallback to iso-8859-1 for robustness
        return json.loads(body_bytes.decode("iso-8859-1"))


def make_headers_recorder(dest_dict):
    """Return a HEADERFUNCTION that records headers in a case-insensitive dict.
       Multi-valued headers are recorded as a list."""
    def header_function(header_line):
        try:
            line = header_line.decode("iso-8859-1")
        except Exception:
            line = str(header_line)
        if ":" not in line:
            return
        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()
        if name in dest_dict:
            if isinstance(dest_dict[name], list):
                dest_dict[name].append(value)
            else:
                dest_dict[name] = [dest_dict[name], value]
        else:
            dest_dict[name] = value
    return header_function


class PycurlBase(unittest.TestCase):
    def setUp(self):
        # temp dir for cookie jars, upload files, etc.
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def new_curl(self):
        c = pycurl.Curl()
        # Set a reasonable timeout for all requests
        c.setopt(c.TIMEOUT, 30)
        # CA bundle when available (safe to set even for HTTP; libcurl ignores)
        if CAINFO_PATH is not None:
            c.setopt(c.CAINFO, CAINFO_PATH)
        # A distinct user agent so servers/logs can identify test traffic
        c.setopt(c.USERAGENT, "pycurl-unittest-suite/1.0 (+python)")
        return c


class TestPycurlVersion(PycurlBase):
    def test_version_and_info(self):
        self.assertIsInstance(pycurl.version, str)
        self.assertTrue(len(pycurl.version) > 0)
        vi = pycurl.version_info()
        self.assertIsInstance(vi, tuple)
        self.assertGreaterEqual(len(vi), 5)
        # libcurl version string present
        self.assertIsInstance(vi[0], str)


class TestFileProtocol(PycurlBase):
    def test_file_url_read(self):
        # Create a small file and read it back using file://
        p = os.path.join(self.tmpdir.name, "hello.txt")
        content = b"hello via file://\nline2\n"
        with open(p, "wb") as f:
            f.write(content)

        buf = BytesIO()
        headers = {}
        c = self.new_curl()
        c.setopt(c.URL, "file://" + p)
        c.setopt(c.WRITEDATA, buf)
        c.setopt(c.NOPROGRESS, True)
        # Header callback won't receive HTTP headers for file://, but it should not error.
        c.setopt(c.HEADERFUNCTION, make_headers_recorder(headers))
        c.perform()
        c.close()

        self.assertEqual(buf.getvalue(), content)


class TestHTTPBasics(PycurlBase):
    @network_required
    def test_http_get(self):
        buf = BytesIO()
        headers = {}
        c = self.new_curl()
        c.setopt(c.URL, HTTPBIN + "/get?foo=bar")
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.HEADERFUNCTION, make_headers_recorder(headers))
        c.perform()

        status = c.getinfo(c.RESPONSE_CODE)
        eff_url = c.getinfo(c.EFFECTIVE_URL)
        total_time = c.getinfo(c.TOTAL_TIME)
        content_type = c.getinfo(c.CONTENT_TYPE)
        c.close()

        self.assertEqual(status, 200)
        self.assertIn("http", eff_url)
        self.assertGreater(total_time, 0.0)
        self.assertTrue(content_type is None or "json" in content_type.lower())

        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["args"].get("foo"), "bar")

    @https_required
    def test_https_get_with_certifi(self):
        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/get")
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        self.assertEqual(c.getinfo(c.RESPONSE_CODE), 200)
        self.assertTrue(c.getinfo(c.TOTAL_TIME) > 0)
        c.close()

    @network_required
    def test_follow_redirects(self):
        # Redirect to https endpoint
        target = HTTPBINS + "/get"
        url = HTTPBIN + "/redirect-to?url=" + target
        c = self.new_curl()
        c.setopt(c.URL, url)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.MAXREDIRS, 5)
        c.perform()
        eff = c.getinfo(c.EFFECTIVE_URL)
        code = c.getinfo(c.RESPONSE_CODE)
        c.close()
        self.assertEqual(code, 200)
        self.assertTrue(eff.startswith(HTTPBINS))

    @network_required
    def test_headers_callback_collects(self):
        buf = BytesIO()
        headers = {}
        c = self.new_curl()
        c.setopt(c.URL, HTTPBIN + "/get")
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.HEADERFUNCTION, make_headers_recorder(headers))
        c.perform()
        c.close()
        # Expect at least server and content-type (names are case-insensitive and may vary)
        self.assertTrue(any(k in headers for k in ("server", "content-type", "date")))

    @network_required
    def test_timeout_and_error(self):
        # Hit a delayed endpoint with a very small timeout to force CURLE_OPERATION_TIMEDOUT
        c = self.new_curl()
        c.setopt(c.URL, HTTPBIN + "/delay/3")
        c.setopt(c.TIMEOUT, 1)  # seconds
        with self.assertRaises(pycurl.error) as ctx:
            c.perform()
        c.close()
        # Validate timeout-ish error (code may vary across libcurl builds; accept timeouts)
        err = ctx.exception
        self.assertIsInstance(err, pycurl.error)
        # Common timeout error codes:
        self.assertIn(err.args[0], (pycurl.E_OPERATION_TIMEDOUT, pycurl.E_OPERATION_TIMEOUTED, 28))


class TestHTTPMethodsAndBody(PycurlBase):
    @network_required
    def test_postfields_urlencoded(self):
        try:
            from urllib.parse import urlencode
        except ImportError:
            from urllib import urlencode
        post_data = {"alpha": "β", "num": "123"}
        body = urlencode(post_data)

        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/post")
        c.setopt(c.POSTFIELDS, body)
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()

        data = decode_body_to_json(buf.getvalue())
        # 'form' contains urlencoded fields parsed by httpbin
        self.assertEqual(data["form"].get("alpha"), "β")
        self.assertEqual(data["form"].get("num"), "123")

    @network_required
    def test_custom_request_patch(self):
        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/patch")
        c.setopt(c.CUSTOMREQUEST, "PATCH")
        c.setopt(c.POSTFIELDS, "payload=data")
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()
        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["method"], "PATCH")

    @network_required
    def test_put_upload_buffer(self):
        payload = b'{"json": true, "n": 42}'
        src = BytesIO(payload)

        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/put")
        c.setopt(c.UPLOAD, 1)
        c.setopt(c.READDATA, src)
        c.setopt(c.INFILESIZE, len(payload))
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()
        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["data"], payload.decode("utf-8"))

    @network_required
    def test_multipart_upload_buffer(self):
        # Upload an in-memory "file" via multipart/form-data
        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/post")
        c.setopt(c.HTTPPOST, [
            ("fileupload", (
                c.FORM_BUFFER, "readme.txt",
                c.FORM_BUFFERPTR, "This is a fancy readme file",
                c.FORM_CONTENTTYPE, "text/plain",
            )),
            ("note", (None, "hello")),  # simple field
        ])
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()
        data = decode_body_to_json(buf.getvalue())
        # httpbin returns files and form fields separately
        self.assertEqual(data["files"].get("fileupload"), "This is a fancy readme file")
        self.assertEqual(data["form"].get("note"), "hello")

    @network_required
    def test_write_to_file(self):
        # Demonstrate WRITEDATA to file handle (binary mode!)
        outp = os.path.join(self.tmpdir.name, "out.bin")
        with open(outp, "wb") as f:
            c = self.new_curl()
            c.setopt(c.URL, HTTPBIN + "/bytes/256")
            c.setopt(c.WRITEDATA, f)
            c.perform()
            self.assertEqual(c.getinfo(c.RESPONSE_CODE), 200)
            c.close()
        self.assertEqual(os.path.getsize(outp), 256)


class TestCookiesAndHeaders(PycurlBase):
    @network_required
    def test_cookies_roundtrip_with_jar(self):
        cookie_jar = os.path.join(self.tmpdir.name, "cookies.txt")
        # 1. Request that sets a cookie and writes cookie jar
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/cookies/set?foo=bar")
        c.setopt(c.COOKIEJAR, cookie_jar)
        c.perform()
        c.close()
        self.assertTrue(os.path.exists(cookie_jar))
        self.assertGreater(os.path.getsize(cookie_jar), 0)

        # 2. New handle reads cookie jar and sends cookie back
        buf = BytesIO()
        c2 = self.new_curl()
        c2.setopt(c2.COOKIEFILE, cookie_jar)
        c2.setopt(c2.URL, HTTPBINS + "/cookies")
        c2.setopt(c2.WRITEDATA, buf)
        c2.perform()
        c2.close()
        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["cookies"].get("foo"), "bar")

    @network_required
    def test_custom_headers(self):
        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/headers")
        c.setopt(c.HTTPHEADER, [
            "X-Test-Header: abc123",
            "Accept: application/json",
        ])
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()
        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["headers"].get("X-Test-Header"), "abc123")


class TestCallbacks(PycurlBase):
    @network_required
    def test_debugfunction_receives_events(self):
        events = []

        def debug_cb(debug_type, debug_msg):
            # Store a subset to keep memory in check
            events.append(int(debug_type))

        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/get")
        c.setopt(c.VERBOSE, True)
        c.setopt(c.DEBUGFUNCTION, debug_cb)
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        c.close()

        self.assertTrue(len(events) > 0)

    @network_required
    def test_progress_or_xferinfo_callback(self):
        calls = {"count": 0}

        # Prefer modern XFERINFOFUNCTION if available; otherwise fallback to PROGRESSFUNCTION.
        if hasattr(pycurl, "XFERINFOFUNCTION"):
            def xferinfo(dltotal, dlnow, ultotal, ulnow):
                calls["count"] += 1
            cb_flag = "XFERINFOFUNCTION"
            cb_value = xferinfo
        else:
            def progress(dltotal, dlnow, ultotal, ulnow):
                calls["count"] += 1
            cb_flag = "PROGRESSFUNCTION"
            cb_value = progress

        # Download a slightly larger payload to ensure multiple callback invocations.
        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBINS + "/bytes/262144")  # 256 KiB
        c.setopt(c.WRITEDATA, buf)
        c.setopt(c.NOPROGRESS, False)
        c.setopt(getattr(c, cb_flag), cb_value)
        c.perform()
        c.close()

        self.assertTrue(calls["count"] > 0, "Progress/Xferinfo callback should have been called.")

    @network_required
    def test_read_and_seek_functions_optional(self):
        # These callbacks are more commonly used for retryable uploads; we attach them and
        # simply verify they don't break a normal GET request.
        seek_calls = {"count": 0}
        read_calls = {"count": 0}

        def seek_cb(offset, whence):
            # Just acknowledge the seek; report OK (0)
            seek_calls["count"] += 1
            return 0

        def read_cb(size):
            # Not used for GET; should not be called. If called, return empty bytes.
            read_calls["count"] += 1
            return b""

        buf = BytesIO()
        c = self.new_curl()
        c.setopt(c.URL, HTTPBIN + "/get")
        c.setopt(c.WRITEDATA, buf)
        c.setopt(c.SEEKFUNCTION, seek_cb)
        c.setopt(c.READFUNCTION, read_cb)
        c.perform()
        c.close()
        # We don't assert counts (libcurl is free to call or not); the main goal is to exercise the setters.


class TestMultiAndShare(PycurlBase):
    @network_required
    def test_multi_interface_parallel_gets(self):
        # Two concurrent transfers via Multi interface
        urls = [HTTPBIN + "/delay/1", HTTPBIN + "/get?i=2"]
        bufs = [BytesIO(), BytesIO()]
        handles = []

        for url, b in zip(urls, bufs):
            c = self.new_curl()
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, b)
            handles.append(c)

        m = pycurl.CurlMulti()
        for h in handles:
            m.add_handle(h)

        # Drive the transfers
        num_handles = len(handles)
        while num_handles:
            while True:
                ret, num_handles = m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break
            if num_handles:
                # Wait for activity or a small timeout
                m.select(1.0)

        # Remove and close
        for h in handles:
            self.assertEqual(h.getinfo(h.RESPONSE_CODE), 200)
            m.remove_handle(h)
            h.close()
        m.close()
        # Validate that we received bodies
        for b in bufs:
            self.assertGreater(len(b.getvalue()), 0)

    @network_required
    def test_share_interface_for_cookies_and_dns(self):
        # Create a Share object and enable sharing of DNS & Cookies
        sh = pycurl.CurlShare()
        # Not all libcurl builds support all share options; guard with hasattr
        if hasattr(sh, "setopt"):
            # These options exist on the Curl handle as constants
            if hasattr(pycurl, "LOCK_DATA_COOKIE"):
                sh.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_COOKIE)
            if hasattr(pycurl, "LOCK_DATA_DNS"):
                sh.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)

        # Prepare a cookie jar used by both handles via SHARE option
        cookie_jar = os.path.join(self.tmpdir.name, "shared_cookies.txt")

        def make_handle():
            c = self.new_curl()
            c.setopt(c.URL, HTTPBINS + "/cookies")
            c.setopt(c.SHARE, sh)
            c.setopt(c.COOKIEJAR, cookie_jar)
            c.setopt(c.COOKIEFILE, cookie_jar)
            return c

        # Set a cookie with h1
        h1 = self.new_curl()
        h1.setopt(h1.URL, HTTPBINS + "/cookies/set?shared=yes")
        h1.setopt(h1.SHARE, sh)
        h1.setopt(h1.COOKIEJAR, cookie_jar)
        h1.perform()
        h1.close()

        # Read cookies with h2
        buf = BytesIO()
        h2 = make_handle()
        h2.setopt(h2.WRITEDATA, buf)
        h2.perform()
        h2.close()

        data = decode_body_to_json(buf.getvalue())
        self.assertEqual(data["cookies"].get("shared"), "yes")


if __name__ == "__main__":
    # A helpful note when HTTPS tests are skipped due to missing certifi:
    if NETWORK_AVAILABLE and CAINFO_PATH is None:
        sys.stderr.write(
            "Note: certifi not found; HTTPS tests that require CA bundle will be skipped.\n"
        )
    unittest.main(verbosity=2)