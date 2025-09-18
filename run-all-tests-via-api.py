#!/usr/bin/env python3

import argparse
import json
import os
import sys
import tempfile
import time
import socket
import ssl
import http.client
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote, urlparse


def _default_port_for_scheme(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _host_header(hostname: str, port: Optional[int], scheme: str) -> str:
    default_port = _default_port_for_scheme(scheme)
    if port and port != default_port:
        return f"{hostname}:{port}"
    return hostname


class _ResolvedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, resolved_host: str, port: int, timeout: float) -> None:
        super().__init__(host=resolved_host, port=port, timeout=timeout)
        self._resolved_host = resolved_host

    # For HTTP we just connect to the resolved host as usual.


class _ResolvedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, resolved_host: str, port: int, timeout: float, *, server_hostname: str, context: Optional[ssl.SSLContext] = None) -> None:
        # Pass the resolved host/IP to the base class so it doesn't try to resolve
        super().__init__(host=resolved_host, port=port, timeout=timeout, context=context)
        self._resolved_host = resolved_host
        self._server_hostname = server_hostname

    def connect(self) -> None:
        # Largely mirrors the stdlib implementation but pins the TCP connect
        # to the resolved host/IP and sets SNI to the original hostname.
        self.sock = socket.create_connection((self._resolved_host, self.port), self.timeout, self.source_address)
        if self._tunnel_host:
            self._tunnel()
        # Ensure we have a context
        if self._context is None:
            self._context = ssl.create_default_context()
        # Enable hostname checking by default
        self._context.check_hostname = True
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self._server_hostname)


def http_get_text(url: str, *, resolve_ip: Optional[str], timeout: float) -> Tuple[int, str]:
    """Perform a GET request with optional DNS override and SNI support.

    If resolve_ip is given, connects to that IP, sets the Host header to the
    original hostname, and (for HTTPS) uses SNI with the original hostname.
    Returns (status_code, text_body).
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "http").lower()
    hostname = parsed.hostname or ""
    port = parsed.port or _default_port_for_scheme(scheme)
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    headers = {
        "Accept": "*/*",
    }

    # If we override resolution, set the Host header explicitly
    if resolve_ip:
        headers["Host"] = _host_header(hostname, parsed.port, scheme)

    try:
        if resolve_ip:
            if scheme == "https":
                context = ssl.create_default_context()
                conn = _ResolvedHTTPSConnection(resolve_ip, port, timeout, server_hostname=hostname, context=context)
            else:
                conn = _ResolvedHTTPConnection(resolve_ip, port, timeout)
        else:
            # No override — use stdlib conveniences
            if scheme == "https":
                conn = http.client.HTTPSConnection(hostname, port, timeout=timeout)
            else:
                conn = http.client.HTTPConnection(hostname, port, timeout=timeout)

        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", errors="replace")
        status = resp.status
        conn.close()
        return status, data
    except Exception as e:
        # Normalize into a network error string like urllib would give
        return 0, f"Network error calling {url}: {e}"


def fetch_tests(base_url: str, *, resolve_ip: Optional[str]) -> List[str]:
    status, body = http_get_text(base_url + "/list", resolve_ip=resolve_ip, timeout=20)
    if status != 200:
        raise RuntimeError(f"/list returned HTTP {status}")
    payload = json.loads(body)
    tests = payload.get("tests", [])
    if not isinstance(tests, list):
        raise RuntimeError("Invalid /list payload: missing 'tests' list")
    return [str(t) for t in tests]


def run_single_test(base_url: str, test_name: str, timeout: float, *, resolve_ip: Optional[str]) -> Tuple[bool, str]:
    url = base_url + "/check/" + quote(test_name)
    try:
        print(f"Checking: {url}")
        status, output = http_get_text(url, resolve_ip=resolve_ip, timeout=timeout)
        ok = status == 200
        return ok, output
    except Exception as e:
        return False, f"Network error calling {url}: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all tests via FastAPI endpoints, sequentially."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "http://127.0.0.1"),
        help="Server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 8081)),
        help="Server port (default: 8081)",
    )
    parser.add_argument(
        "--outdir",
        default=tempfile.mkdtemp(prefix="api-test-logs_"),
        help="Directory to write per-test logs.",
    )

    parser.add_argument(
        "--test-timeout",
        type=float,
        default=30.0,
        help="Timeout for each test in seconds (default: 30.0)",
    )

    parser.add_argument(
        "--resolve-ip",
        default=os.environ.get("RESOLVE_IP"),
        help=(
            "Optional IP to resolve the server hostname to. "
            "When set, connections go to this IP while preserving the original "
            "hostname for HTTP Host and TLS SNI (SNI-compatible)."
        ),
    )

    args = parser.parse_args()

    host_value = args.host
    if not (host_value.startswith("http://") or host_value.startswith("https://")):
        host_value = "http://" + host_value
    base_url = f"{host_value}:{args.port}"
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tests = fetch_tests(base_url, resolve_ip=args.resolve_ip)
    if not tests:
        print("No tests returned by /list. Nothing to run.")
        return 0

    print(
        f"Discovered {len(tests)} tests. Output for each test will be stored at: '{args.outdir}'. Running sequentially...\n"
    )

    passed: list[str] = []
    failed: list[str] = []

    for idx, test in enumerate(tests, start=1):
        print(f"[{idx}/{len(tests)}] Running {test} ...", flush=True)
        ok, output = run_single_test(base_url, test, timeout=args.test_timeout, resolve_ip=args.resolve_ip)
        # Write log
        safe_name = test.replace(os.sep, "_")
        log_path = outdir / f"{safe_name}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)

        if ok:
            print(f"  PASS: {test} -> {log_path}")
            passed.append(test)
        else:
            print(f"  FAIL: {test} -> {log_path}")
            failed.append(test)

    print("\nSummary:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print("  Failed tests:")
        for t in failed:
            print(f"    - {t}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
