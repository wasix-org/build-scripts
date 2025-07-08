import asyncio
import uvloop

# Install uvloop as the default event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def test_tcp_echo_server():
    print("Testing TCP echo server...")

    async def handle_echo(reader, writer):
        data = await reader.read(100)
        writer.write(data)
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async def client():
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
        message = b'hello'
        writer.write(message)
        await writer.drain()
        data = await reader.read(100)
        assert data == message, "Echo response mismatch"
        writer.close()
        await writer.wait_closed()

    await asyncio.gather(client(), return_exceptions=False)
    server.close()
    await server.wait_closed()
    print("Passed: TCP echo server")

async def main():
    await test_tcp_echo_server()
    print("✅ All uvloop tests passed.")

if __name__ == "__main__":
    asyncio.run(main())