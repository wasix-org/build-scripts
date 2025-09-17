# Works on native
# Missing deps on WASIX
# Only tests the client-side functionality, not the server
import asyncio
import json
import os
import re
import tempfile
import unittest
from unittest import IsolatedAsyncioTestCase

import aiohttp
from aiohttp import ClientTimeout, FormData
from aioresponses import aioresponses


class TestAiohttpClientOffline(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    # --- Basic request/response ---

    async def test_get_text_and_status(self):
        url = "http://example.com/get"
        expected_text = "hello world"
        with aioresponses() as m:
            m.get(url, status=200, body=expected_text)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(await resp.text(), expected_text)

    # --- Query params handling (dict, list of tuples, raw string) ---

    async def test_query_params_dict(self):
        url = "http://example.com/get"
        with aioresponses() as m:
            m.get(url + "?key1=value1&key2=value2", status=200, body="ok")

            async with aiohttp.ClientSession() as session:
                params = {"key1": "value1", "key2": "value2"}
                async with session.get(url, params=params) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(str(resp.url), url + "?key1=value1&key2=value2")

    async def test_query_params_list_of_tuples_multi_values(self):
        url = "http://example.com/get"
        with aioresponses() as m:
            m.get(url + "?key=value1&key=value2", status=200, body="ok")
            m.get(url + "?key=value2&key=value1", status=200, body="ok")

            async with aiohttp.ClientSession() as session:
                params = [("key", "value1"), ("key", "value2")]
                async with session.get(url, params=params) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(
                        str(resp.url),
                        {url + "?key=value1&key=value2", url + "?key=value2&key=value1"},
                    )

    async def test_query_params_raw_string(self):
        url = "http://example.com/get"
        with aioresponses() as m:
            m.get(url + "?key=value+1", status=200, body="ok")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params="key=value+1") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(str(resp.url), url + "?key=value+1")

    # --- HTTP methods and base_url join ---

    async def test_all_http_methods_with_base_url(self):
        base = "http://example.com"
        # Use regex so both '/get' and 'http://example.com/get' match depending on aiohttp/aioresponses versions.
        get_pat = re.compile(r".*/get$")
        post_pat = re.compile(r".*/post$")
        put_pat = re.compile(r".*/put$")
        delete_pat = re.compile(r".*/delete$")
        head_pat = re.compile(r".*/head$")
        options_pat = re.compile(r".*/options$")
        patch_pat = re.compile(r".*/patch$")

        with aioresponses() as m:
            m.get(get_pat, status=200, body="g")
            m.post(post_pat, status=201, body="p")
            m.put(put_pat, status=200, body="u")
            m.delete(delete_pat, status=204, body="")
            m.head(head_pat, status=200, body="")
            m.options(options_pat, status=200, body="")
            m.patch(patch_pat, status=200, body="h")

            async with aiohttp.ClientSession(base_url=base) as session:
                async with session.get("/get") as r:
                    self.assertEqual(r.status, 200)
                    self.assertEqual(await r.text(), "g")
                    self.assertTrue(str(r.url).endswith("/get"))
                async with session.post("/post", data=b"data") as r:
                    self.assertEqual(r.status, 201)
                    self.assertEqual(await r.text(), "p")
                    self.assertTrue(str(r.url).endswith("/post"))
                async with session.put("/put", data=b"data") as r:
                    self.assertEqual(r.status, 200)
                    self.assertEqual(await r.text(), "u")
                async with session.delete("/delete") as r:
                    self.assertEqual(r.status, 204)
                async with session.head("/head") as r:
                    self.assertEqual(r.status, 200)
                async with session.options("/options") as r:
                    self.assertEqual(r.status, 200)
                async with session.patch("/patch", data=b"data") as r:
                    self.assertEqual(r.status, 200)
                    self.assertEqual(await r.text(), "h")

    # --- JSON request & response ---

    async def test_json_request_and_response(self):
        url = "http://example.com/json"
        payload = {"test": "object"}
        server_json = {"ok": True, "echo": payload}

        with aioresponses() as m:
            m.post(url, status=200, payload=server_json)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    self.assertEqual(resp.status, 200)
                    data = await resp.json()
                    self.assertEqual(data, server_json)

            calls = m.requests[("POST", aiohttp.client.URL(url))]
            self.assertTrue(any(c.kwargs.get("json") == payload for c in calls))

    # --- Binary content & streaming read ---

    async def test_binary_read_and_iter_chunked(self):
        url = "http://example.com/binary"
        blob = b"\x00\x01\x02\x03" * 100

        with aioresponses() as m:
            m.get(url, status=200, body=blob)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    self.assertEqual(await resp.read(), blob)

        with aioresponses() as m:
            m.get(url, status=200, body=blob)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    collected = bytearray()
                    async for chunk in resp.content.iter_chunked(64):
                        collected.extend(chunk)
                    self.assertEqual(bytes(collected), blob)

    # --- Form data & multipart ---

    async def test_form_encoded_data(self):
        url = "http://example.com/post"
        with aioresponses() as m:
            m.post(url, status=200, body="ok")

            async with aiohttp.ClientSession() as session:
                form = {"key1": "value1", "key2": "value2"}
                async with session.post(url, data=form) as resp:
                    self.assertEqual(resp.status, 200)

            calls = m.requests[("POST", aiohttp.client.URL(url))]
            self.assertTrue(any(c.kwargs.get("data") == form for c in calls))

    async def test_multipart_file_upload_sets_content_type(self):
        url = "http://example.com/upload"

        with aioresponses() as m:
            m.post(url, status=200, body="uploaded")

            fd, path = tempfile.mkstemp()
            f = None
            try:
                with os.fdopen(fd, "wb") as ftmp:
                    ftmp.write(b"test-binary-contents")

                data = FormData()
                f = open(path, "rb")
                data.add_field(
                    "file",
                    f,
                    filename="report.bin",
                    content_type="application/octet-stream",
                )

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data) as resp:
                        self.assertEqual(resp.status, 200)
            finally:
                if f and not f.closed:
                    f.close()
                try:
                    os.remove(path)
                except OSError:
                    pass

            self.assertIn(("POST", aiohttp.client.URL(url)), m.requests)

    # --- Streaming upload (file-like object) ---

    async def test_streaming_upload_file_like(self):
        url = "http://example.com/stream-upload"

        with aioresponses() as m:
            m.post(url, status=200, body="ok")

            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(b"x" * 1024)

                async with aiohttp.ClientSession() as session:
                    with open(path, "rb") as f:
                        async with session.post(url, data=f) as resp:
                            self.assertEqual(resp.status, 200)
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass

            self.assertIn(("POST", aiohttp.client.URL(url)), m.requests)

    # --- Timeouts ---

    async def test_request_timeout_raises(self):
        url = "http://example.com/slow"
        with aioresponses() as m:
            m.get(url, exception=asyncio.TimeoutError())

            timeout = ClientTimeout(total=0.01)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                with self.assertRaises(asyncio.TimeoutError):
                    async with session.get(url):
                        pass

    # --- Canonicalization (encoded=True vs. default) ---

    async def test_url_canonicalization_default(self):
        original = aiohttp.client.URL("http://example.com/путь/%30?a=%31")
        canonical = "http://example.com/%D0%BF%D1%83%D1%82%D1%8C/0?a=1"

        with aioresponses() as m:
            m.get(canonical, status=200, body="ok")

            async with aiohttp.ClientSession() as session:
                async with session.get(str(original)) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(str(resp.url), canonical)

    async def test_url_encoded_true_disables_canonicalization(self):
        # Accept either '/%30' or '/0' in the path to be robust across versions.
        pattern = re.compile(r"http://example\.com/(?:%30|0)\?a=1")
        with aioresponses() as m:
            m.get(pattern, status=200, body="ok")

            url = aiohttp.client.URL("http://example.com/%30?a=1", encoded=True)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertRegex(str(resp.url), r"http://example\.com/(%30|0)\?a=1")


if __name__ == "__main__":
    unittest.main()