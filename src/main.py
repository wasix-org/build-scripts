import contextlib
import io
import os
import runpy
import sys

from fastapi import FastAPI, Response


class Tee(io.StringIO):
    def __init__(self, *streams):
        super().__init__()
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
        super().write(data)


app = FastAPI(
    title="Build Scripts - Tests",
    description="This API wraps the existing run-scripts.py and simply calls it. This allows us to ensure that all tested packages works at any given time.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "Build Scripts - Tests. Be aware that calling /check will take anywhere from 3-5 minutes to deliver a response. Look in the dashboard logs for progress.",
        "version": "0.1.0",
        "endpoints": [
            "/",
            "/list",
            "/check",
            "/check/{test_name}",
        ],
    }


import traceback


def _resolve_run_tests_path() -> str:
    # Prefer explicit env, fall back to local file
    return os.environ.get(
        "RUN_TESTS_PATH",
        os.path.join(os.path.dirname(__file__), "run-tests.py"),
    )


def _resolve_tests_dir() -> str:
    # Prefer explicit env, otherwise tests/ at repo root
    default = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "tests")
    )
    return os.environ.get("TEST_DIR", default)


def _list_tests() -> list[str]:
    import glob

    tests_dir = _resolve_tests_dir()
    pattern = os.path.join(tests_dir, "*.py")
    files = [f for f in glob.glob(pattern) if ".skip" not in f and ".broken" not in f]
    # Return just filenames for readability
    return [os.path.basename(f) for f in sorted(files)]


@app.get("/list")
async def list_tests():
    tests = _list_tests()
    return {"count": len(tests), "tests": tests}


@app.get("/check")
async def check_packages():
    """
    Check packages by running the run-tests.py file and capture output.
    It's done this way to allow the run-tests.py to also be run as
    standalone script (and since I don't have time to refactor this
    into a fully-fleged fastapi project)
    """
    buf = Tee(sys.stdout)
    try:
        with contextlib.redirect_stdout(buf):
            # Ensure run-tests.py can find tests and use correct path
            os.environ["TEST_DIR"] = _resolve_tests_dir() + "/"
            runpy.run_path(_resolve_run_tests_path())
        output = buf.getvalue()
        return Response(content=output, status_code=200)
    except SystemExit as e:
        output = buf.getvalue()
        print(output)
        if e.code == 0:
            return Response(content=output, status_code=200)
        else:
            # Return status code 417 "Expectation failed", which is probably best fit
            # even though we dont process any headers
            return Response(content=output, status_code=417)
    except Exception:
        output = buf.getvalue()
        tb = traceback.format_exc()
        print(output)
        print(tb)
        return Response(content=output + "\n" + tb, status_code=500)


@app.get("/check/{test_name}")
async def check_single(test_name: str):
    """
    Run a single test file by name.

    Accepts either exact filename (e.g., requests-test.py) or the base name
    (e.g., requests-test). Only tests present in the tests directory are allowed.
    """
    tests_dir = _resolve_tests_dir()
    available = set(_list_tests())

    # Normalize input to a filename present in available
    candidates = []
    if test_name.endswith(".py"):
        candidates.append(test_name)
    else:
        candidates.append(f"{test_name}.py")

    # Keep candidates that exist in available tests
    chosen = None
    for c in candidates:
        if c in available:
            chosen = c
            break

    if not chosen:
        return Response(
            content=f"Test '{test_name}' not found. Use /list to see available tests.",
            status_code=404,
        )

    test_path = os.path.join(tests_dir, chosen)

    # Prepare argv for run-tests.py to run a single file
    buf = Tee(sys.stdout)
    try:
        with contextlib.redirect_stdout(buf):
            old_argv = sys.argv[:]
            try:
                # Here we're calling "run-tests.py" with arguments for the
                # specific test. SO we need to resolve the script as arg0 and
                # then set the specific test  to run as arg1
                sys.argv = [
                    _resolve_run_tests_path(),
                    test_path,
                ]
                # Then we actually run the script
                # Suboptimal, organicly grown spagetti
                runpy.run_path(_resolve_run_tests_path())
            finally:
                sys.argv = old_argv
        output = buf.getvalue()
        return Response(content=output, status_code=200)
    except SystemExit as e:
        output = buf.getvalue()
        print(f"Code: {e.code}, output: ")
        if e.code == 0:
            return Response(content=output, status_code=200)
        else:
            return Response(content=output, status_code=417)
    except Exception:
        output = buf.getvalue()
        tb = traceback.format_exc()
        print(output)
        print(tb)
        return Response(content=output + "\n" + tb, status_code=500)


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host=host, port=port)
