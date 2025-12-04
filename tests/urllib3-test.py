import unittest
import urllib3
import certifi
import socket
import pytest
from urllib3.exceptions import MaxRetryError, NameResolutionError

def _has_network() -> bool:
    try:
        socket.getaddrinfo("httpbin.org", 443)
        return True
    except Exception:
        return False


HAS_NET = _has_network()


@pytest.mark.skipif(not HAS_NET, reason="Network restricted in test environment")
class TestUrllib3Basic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a PoolManager with certificate verification
        cls.http = urllib3.PoolManager(
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where()
        )

    def test_get_request(self):
        resp = self.http.request("GET", "https://httpbin.org/get")
        self.assertEqual(resp.status, 200)
        data = resp.json()
        self.assertIn("url", data)

    def test_get_with_params(self):
        resp = self.http.request("GET", "https://httpbin.org/get", fields={"foo": "bar"})
        self.assertEqual(resp.status, 200)
        data = resp.json()
        self.assertEqual(data["args"]["foo"], "bar")

    def test_post_form(self):
        resp = self.http.request("POST", "https://httpbin.org/post", fields={"hello": "world"})
        self.assertEqual(resp.status, 200)
        data = resp.json()
        self.assertEqual(data["form"]["hello"], "world")

    def test_post_json(self):
        resp = self.http.request(
            "POST",
            "https://httpbin.org/post",
            json={"key": "value"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status, 200)
        data = resp.json()
        self.assertEqual(data["json"]["key"], "value")

    def test_custom_headers(self):
        resp = self.http.request(
            "GET",
            "https://httpbin.org/headers",
            headers={"X-Test": "foobar"},
        )
        self.assertEqual(resp.status, 200)
        data = resp.json()
        self.assertEqual(data["headers"]["X-Test"], "foobar")

    def test_binary_content(self):
        resp = self.http.request("GET", "https://httpbin.org/bytes/4")
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.data), 4)  # exactly 4 random bytes

    def test_retries_disabled(self):
        # When DNS fails and retries are disabled, urllib3 may raise either
        # NameResolutionError (newer) or MaxRetryError (older/depending on path).
        with self.assertRaises((NameResolutionError, MaxRetryError)):
            self.http.request("GET", "https://nx.example.com", retries=False)


if __name__ == "__main__":
    unittest.main()
