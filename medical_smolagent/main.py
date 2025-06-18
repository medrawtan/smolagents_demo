from smolagents import ToolCollection, CodeAgent, LiteLLMModel

# 配置本地 Ollama 模型
model = LiteLLMModel(
    model_id="ollama/qwen3:8b",  # 添加 ollama/ 前缀指定提供者
    api_base="http://localhost:11434",  # Ollama 默认地址
    api_key="ollama",  # Ollama 不需要密钥，但需要提供非空值
    num_ctx=8192,  # 上下文长度
    timeout=120,    # 增加超时时间
)

# 配置Streamable HTTP MCP服务器参数
server_parameters = {
    "url": "https://evalstate-hf-mcp-server.hf.space/mcp",
    "transport": "streamable-http"
}

def test_mcp_tools():
    """测试MCP搜索工具"""
    print("测试MCP搜索工具...")
    
    try:
        # 使用上下文管理器从MCP服务器加载工具集合
        with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
            # 创建CodeAgent实例并使用从MCP服务器加载的工具
            agent = CodeAgent(
                tools=[*tool_collection.tools], 
                add_base_tools=True, 
                model=model
            )
            
            # 测试查询
            test_queries = [
                "糖尿病最新治疗方法",
                "COVID-19 症状",
                "心脏搭桥手术"
            ]
            
            for query in test_queries:
                print(f"\n{'='*50}")
                print(f"测试查询: {query}")
                
                try:
                    result = agent.run(query)
                    print(f"\nMCP 搜索结果:")
                    print(result)
                except Exception as e:
                    print(f"查询 '{query}' 时出错: {str(e)}")
                
                input("按 Enter 继续测试下一个查询...")
    except Exception as e:
        print(f"初始化测试环境时出错: {str(e)}")

def main():
    """主函数"""
    try:
        # 测试MCP工具
        test_mcp_tools()
        
        print("\n医疗智能体初始化完成！")
        print("输入您的问题，或输入 'exit' 退出")
        
        # 交互式循环
        while True:
            try:
                query = input("\n> ").strip()
                
                if query.lower() in ['exit', 'quit', '退出']:
                    print("感谢使用医疗智能体，再见！")
                    break
                    
                if not query:
                    continue
                
                # 使用MCP工具处理查询
                with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
                    # 创建新的agent实例，确保每次查询都是独立的
                    agent = CodeAgent(
                        tools=[*tool_collection.tools], 
                        add_base_tools=True, 
                        model=model
                    )
                    print(f"\n处理查询: {query}")
                    response = agent.run(query)
                    print(f"\n{response}")
                
            except KeyboardInterrupt:
                print("\n检测到中断信号，正在退出...")
                break
            except Exception as e:
                print(f"\n处理查询时出错: {str(e)}")
    
    except Exception as e:
        print(f"程序运行出错: {str(e)}")

if __name__ == "__main__":
    main()