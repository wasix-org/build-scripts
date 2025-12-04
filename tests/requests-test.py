import unittest
import requests
import socket
import pytest

BASE_URL = "https://httpbin.org"


def _has_network() -> bool:
    try:
        socket.getaddrinfo("httpbin.org", 443)
        return True
    except Exception:
        return False


HAS_NET = _has_network()


@pytest.mark.skipif(not HAS_NET, reason="Network restricted in test environment")
class TestRequestsModule(unittest.TestCase):

    def test_get_request(self):
        response = requests.get(f"{BASE_URL}/get", params={"foo": "bar"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("args", data)
        self.assertEqual(data["args"]["foo"], "bar")

    def test_post_request(self):
        payload = {"username": "alice", "password": "secret"}
        response = requests.post(f"{BASE_URL}/post", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["json"], payload)

    def test_put_request(self):
        payload = {"update": "value"}
        response = requests.put(f"{BASE_URL}/put", data=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["form"]["update"], "value")

    def test_delete_request(self):
        response = requests.delete(f"{BASE_URL}/delete")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("url", data)
        self.assertTrue(data["url"].endswith("/delete"))

    def test_headers(self):
        headers = {"Custom-Header": "TestValue"}
        response = requests.get(f"{BASE_URL}/headers", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Custom-Header", data["headers"])
        self.assertEqual(data["headers"]["Custom-Header"], "TestValue")


if __name__ == "__main__":
    unittest.main()
