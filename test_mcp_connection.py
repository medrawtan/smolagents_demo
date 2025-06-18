import asyncio
import aiohttp
import time
import os
from smolagents import ToolCollection

# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

# MCP 服务器配置
SERVER_URL = "https://evalstate-hf-mcp-server.hf.space/mcp"

# 代理设置
PROXY = 'http://127.0.0.1:7890'

async def test_connection():
    """测试 MCP 服务器连接"""
    print("\n" + "="*60)
    print("测试 MCP 服务器连接")
    print("="*60)
    
    start = time.time()
    try:
        # 测试基本连接
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(SERVER_URL, 
                                proxy=PROXY, 
                                timeout=timeout,
                                ssl=False) as resp:
                print(f"✅ 连接成功! 状态码: {resp.status}")
                print(f"   响应时间: {time.time()-start:.2f}秒")
                return True
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. 需要配置代理")
        print("3. 服务器暂时不可用")
        return False

async def test_tools():
    """测试 MCP 工具加载"""
    print("\n" + "="*60)
    print("测试 MCP 工具加载")
    print("="*60)
    
    try:
        server_params = {
            "url": SERVER_URL,
            "transport": "streamable-http",
            "proxies": {
                "http": PROXY,
                "https": PROXY
            }
        }
        
        async with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tools:
            print(f"✅ 成功加载 {len(tools.tools)} 个工具")
            print("\n可用工具:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"{i}. {tool.name} - {tool.description[:50]}...")
            return True
            
    except Exception as e:
        print(f"❌ 工具加载失败: {str(e)}")
        return False

async def main():
    # 测试连接
    if not await test_connection():
        return
    
    # 测试工具加载
    if not await test_tools():
        return
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
