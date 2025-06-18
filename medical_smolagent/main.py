import os
import sys
import argparse
import gradio as gr
from typing import List, Dict, Any, Optional, Union, Tuple
from loguru import logger

from smolagents import ToolCollection, CodeAgent, LiteLLMModel, GradioUI
from medical_smolagent.tools.translation import translate, TranslationTool

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

def setup_logging():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

def translate_response(response: Union[str, Dict, Any]) -> str:
    """将响应翻译成中文"""
    if isinstance(response, dict):
        text = response.get('text', str(response))
    else:
        text = str(response)
        
    if not text.strip():
        return text
        
    # 检测语言
    from medical_smolagent.tools.translation import LanguageDetector
    detected_lang = LanguageDetector.detect_language(text)
    logger.info(f"Detected language: {detected_lang}")
    
    # 如果不是中文，则翻译
    if detected_lang != "Chinese":
        logger.info(f"Translating from {detected_lang} to Chinese")
        try:
            from medical_smolagent.tools.translation import translator
            translated = translator.translate(text, source_lang=detected_lang, target_lang="Chinese")
            return translated
        except Exception as e:
            logger.error(f"Error in translate_response: {str(e)}", exc_info=True)
            return f"{text}\n\n(翻译失败: {str(e)})"
            
    return text

# 全局变量，用于保持MCP连接
_global_tool_collection = None
_global_tools = []  # 初始化为空列表

def initialize_mcp_tools() -> bool:
    """初始化MCP工具集合"""
    global _global_tool_collection, _global_tools
    
    if _global_tool_collection is not None:
        return True  # 已经初始化
        
    try:
        logger.info("Initializing MCP tool collection...")
        logger.debug(f"Using server parameters: {server_parameters}")
        
        # 创建工具集合
        _global_tool_collection = ToolCollection.from_mcp(
            server_parameters, 
            trust_remote_code=True
        )
        
        # 进入上下文
        context = _global_tool_collection.__enter__()
        logger.debug(f"MCP context entered: {context}")
        
        # 获取工具列表
        if hasattr(_global_tool_collection, 'tools'):
            _global_tools = list(_global_tool_collection.tools)  # 转换为列表并保存
            logger.info(f"MCP tool collection initialized successfully with {len(_global_tools)} tools")
            return True
        else:
            logger.error("MCP tool collection has no 'tools' attribute")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize MCP tool collection: {str(e)}", exc_info=True)
        _global_tools = []
        return False

def get_agent() -> CodeAgent:
    """获取配置好的agent实例，并添加翻译功能"""
    # 确保翻译工具已初始化
    from medical_smolagent.tools.translation import translator
    translator.initialize()
    
    # 初始化MCP工具
    initialize_mcp_tools()
    
    # 创建原始agent
    agent = CodeAgent(
        tools=_global_tools,  # 使用缓存的工具列表
        add_base_tools=True,
        model=model
    )
    
    # 保存原始的run方法
    original_run = agent.run
    
    # 保存原始的final_answer函数
    original_final_answer = getattr(agent, 'final_answer', None)
    
    # 定义翻译函数
    def translate_text(text: str) -> str:
        """翻译文本为中文"""
        if not text or any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
        try:
            return translator.translate(text, target_lang="Chinese")
        except Exception as e:
            logger.error(f"翻译响应时出错: {str(e)}")
            return f"{text}\n\n(翻译失败: {str(e)})"
    
    # 重写final_answer方法
    def final_answer_with_translation(answer: str) -> str:
        """包装final_answer，添加翻译功能"""
        translated = translate_text(answer)
        if original_final_answer:
            return original_final_answer(translated)
        return translated
    
    # 替换final_answer方法
    if original_final_answer:
        agent.final_answer = final_answer_with_translation
    
    # 重写run方法，添加翻译功能
    def run_with_translation(query: str, *args, **kwargs) -> str:
        try:
            # 调用原始的run方法
            response = original_run(query, *args, **kwargs)
            
            # 确保响应是字符串
            if not isinstance(response, str):
                response = str(response)
            
            # 如果响应不是中文，尝试翻译
            return translate_text(response)
            
        except Exception as e:
            error_msg = f"执行查询时出错: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    # 替换run方法
    agent.run = run_with_translation
    
    return agent

def run_cli():
    """运行命令行界面"""
    print("\n医疗智能体初始化完成！")
    print("输入您的问题，或输入 'exit' 退出")
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() in ['exit', 'quit', '退出']:
                print("感谢使用医疗智能体，再见！")
                break
                
            if not query:
                continue
            
            print(f"\n处理中，请稍候...")
            
            try:
                # 获取新的agent实例处理查询
                agent = get_agent()
                response = agent.run(query)
                
                # 确保响应是字符串
                if not isinstance(response, str):
                    response = str(response)
                
                print(f"\n{'='*80}")
                print(f"问题: {query}")
                print("-"*80)
                print(f"回答: {response}")
                print("="*80)
                
            except Exception as e:
                error_msg = f"处理查询时出错: {str(e)}"
                print(f"\n{error_msg}")
                logger.error(error_msg)
            
        except KeyboardInterrupt:
            print("\n检测到中断信号，正在退出...")
            break

def run_gradio():
    """运行Gradio Web界面"""
    try:
        # 创建Gradio界面
        with gr.Blocks(title="医疗智能体") as demo:
            gr.Markdown("# 医疗智能体")
            gr.Markdown("输入您的医疗相关问题，智能体将为您提供专业解答。")
            
            with gr.Row():
                chatbot = gr.Chatbot(label="对话历史")
                
            with gr.Row():
                msg = gr.Textbox(
                    label="输入您的问题",
                    placeholder="请输入您的医疗问题...",
                    lines=3
                )
                
            with gr.Row():
                submit_btn = gr.Button("提交")
                clear_btn = gr.Button("清空对话")
            
            def respond(message: str, chat_history: List[Tuple[str, str]] = None) -> Tuple[str, List[Tuple[str, str]]]:
                """处理用户输入并返回响应"""
                if chat_history is None:
                    chat_history = []
                    
                try:
                    # 显示用户消息
                    chat_history.append((message, None))
                    
                    # 获取新的agent实例处理查询
                    agent = get_agent()
                    
                    # 处理查询并获取响应
                    response = agent.run(message)
                    
                    # 确保响应是字符串
                    if not isinstance(response, str):
                        response = str(response)
                    
                    # 更新聊天历史
                    chat_history[-1] = (message, response)
                    
                    return "", chat_history
                    
                except Exception as e:
                    error_msg = f"处理请求时出错: {str(e)}"
                    logger.error(error_msg)
                    chat_history[-1] = (message, error_msg)
                    return "", chat_history
            
            # 设置事件处理
            msg.submit(respond, [msg, chatbot], [msg, chatbot])
            submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
            clear_btn.click(lambda: [], None, chatbot, queue=False)
            
            # 添加自定义CSS
            demo.css = """
            .gradio-container {
                max-width: 900px !important;
                margin: 0 auto !important;
            }
            """
            
        # 启动Gradio界面
        print("\n正在启动Web界面，请稍候...")
        print("如果浏览器没有自动打开，请访问: http://localhost:7860")
        demo.launch(
            share=False, 
            server_name="0.0.0.0", 
            server_port=7860,
            show_error=True
        )
        
    except Exception as e:
        error_msg = f"启动Gradio界面时出错: {str(e)}"
        logger.error(error_msg)
        print(f"\n错误: {error_msg}")
        raise

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='医疗智能体')
    parser.add_argument('--mode', type=str, choices=['cli', 'web'], default='cli',
                      help='运行模式: cli(命令行) 或 web(网页界面)')
    parser.add_argument('--port', type=int, default=7860,
                      help='Web服务器端口 (默认: 7860)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                      help='Web服务器监听地址 (默认: 0.0.0.0)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'web':
            print("\n=== 医疗智能体 Web 界面 ===")
            print(f"服务器将运行在: http://{args.host}:{args.port}")
            print("按 Ctrl+C 停止服务器\n")
            
            # 设置环境变量，供Gradio使用
            os.environ['GRADIO_SERVER_NAME'] = args.host
            os.environ['GRADIO_SERVER_PORT'] = str(args.port)
            
            run_gradio()
        else:
            print("\n=== 医疗智能体 命令行模式 ===")
            print("输入您的问题，智能体会自动搜索最新医学信息并翻译成中文回答。")
            print("输入 'exit' 或按 Ctrl+C 退出\n")
            run_cli()
            
    except KeyboardInterrupt:
        print("\n\n检测到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        print(f"\n错误: 程序运行出错，请检查日志获取详细信息")
        sys.exit(1)
    finally:
        print("\n感谢使用医疗智能体，再见！")

if __name__ == "__main__":
    main()