#!/usr/bin/env python3

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def fetch_tests(base_url: str) -> List[str]:
    with urlopen(base_url + "/list", timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"/list returned HTTP {resp.status}")
        payload = json.loads(resp.read().decode("utf-8"))
        tests = payload.get("tests", [])
        if not isinstance(tests, list):
            raise RuntimeError("Invalid /list payload: missing 'tests' list")
        return [str(t) for t in tests]


def run_single_test(base_url: str, test_name: str, timeout: float) -> Tuple[bool, str]:
    url = base_url + "/check/" + quote(test_name)
    req = Request(url, method="GET")
    try:
        print(f"Checking: {url}")
        with urlopen(req, timeout=timeout) as resp:
            output = resp.read().decode("utf-8", errors="replace")
            ok = resp.status == 200
            return ok, output
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(e)
        # 417 or 500 considered failure
        return False, body
    except URLError as e:
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

    args = parser.parse_args()

    base_url = f"{args.host}:{args.port}"
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tests = fetch_tests(base_url)
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
        ok, output = run_single_test(base_url, test, timeout=args.test_timeout)
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
