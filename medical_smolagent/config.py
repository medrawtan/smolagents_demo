from pydantic import Field
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class AgentConfig(BaseSettings):
    """智能体配置类"""
    model_id: str = Field(default_factory=lambda: os.getenv("MODEL_ID", "ollama_chat/llama3"), description="LLM模型ID")
    api_base: str = Field(default_factory=lambda: os.getenv("API_BASE", "http://localhost:11434"), description="LLM API地址")
    api_key: str = Field(default_factory=lambda: os.getenv("API_KEY", "none"), description="LLM API密钥")
    num_ctx: int = Field(default_factory=lambda: int(os.getenv("NUM_CTX", "8192")), description="上下文窗口大小")
    
    mcp_server_url: str = Field(
        default_factory=lambda: os.getenv(
            "MCP_SERVER_URL", 
            "https://evalstate-hf-mcp-server.hf.space/mcp"
        ), 
        description="MCP服务器地址"
    )
    
    proxy_url: str = Field(
        default_factory=lambda: os.getenv("PROXY_URL", ""), 
        description="代理服务器地址"
    )
    
    translation_api: str = Field(
        default_factory=lambda: os.getenv("TRANSLATION_API", "baidu"), 
        description="翻译API提供商"
    )

# 创建全局配置实例
config = AgentConfig()