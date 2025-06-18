import asyncio
import aiohttp

async def test_connection():
    url = "https://evalstate-hf-mcp-server.hf.space/mcp"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
