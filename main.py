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
        "message": "Build Scripts - Tests",
        "version": "0.1.0",
        "endpoints": [
            "/",
            "/check",
        ],
    }


import traceback


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
            runpy.run_path("/app/run-tests.py")
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


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host=host, port=port)
