import asyncio
import uvloop

# Install uvloop as the default event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def test_sleep():
    print("Testing asyncio.sleep...")
    await asyncio.sleep(0.1)
    print("Passed: asyncio.sleep")

async def test_task_creation():
    print("Testing task creation...")
    async def dummy():
        await asyncio.sleep(0.01)
        return 42

    task = asyncio.create_task(dummy())
    result = await task
    assert result == 42, "Task did not return expected result"
    print("Passed: task creation and execution")

async def main():
    await test_sleep()
    await test_task_creation()
    print("✅ All uvloop tests passed.")

if __name__ == "__main__":
    asyncio.run(main())