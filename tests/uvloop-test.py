import asyncio
import pytest
import uvloop

# Install uvloop as the default event loop policy so asyncio.run uses it
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# Internal async helpers (not collected directly by pytest)
async def _sleep():
    await asyncio.sleep(0.1)


async def _task_creation():
    async def dummy():
        await asyncio.sleep(0.01)
        return 42

    task = asyncio.create_task(dummy())
    result = await task
    assert result == 42, "Task did not return expected result"


async def _tcp_echo_server():
    async def handle_echo(reader, writer):
        data = await reader.read(100)
        writer.write(data)
        await writer.drain()
        writer.close()

    # Use port 0 to avoid conflicts when running under pytest
    try:
        server = await asyncio.start_server(handle_echo, "127.0.0.1", 0)
    except Exception as e:  # Network may be sandboxed/disabled
        pytest.skip(f"Network unavailable for test: {e}")

    if not server.sockets:
        server.close()
        await server.wait_closed()
        pytest.skip("No sockets available (network sandbox)")

    host, port = server.sockets[0].getsockname()[:2]

    async def client():
        reader, writer = await asyncio.open_connection(host, port)
        message = b"hello"
        writer.write(message)
        await writer.drain()
        data = await reader.read(100)
        assert data == message, "Echo response mismatch"
        writer.close()
        await writer.wait_closed()

    await asyncio.gather(client(), return_exceptions=False)
    server.close()
    await server.wait_closed()


# Pytest-compatible sync wrappers
def test_sleep():
    asyncio.run(_sleep())


def test_task_creation():
    asyncio.run(_task_creation())


def test_tcp_echo_server():
    asyncio.run(_tcp_echo_server())


async def main():
    await _sleep()
    await _task_creation()
    await _tcp_echo_server()
    print("✅ All uvloop tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
