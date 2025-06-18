from abc import ABC, abstractmethod
import os
import urllib3
from smolagents import Tool
from loguru import logger
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from medical_smolagent import config

class BaseTool(Tool, ABC):
    """工具基类，封装通用逻辑"""
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query or input text",
            "required": True,
            "nullable": False
        }
    }
    output_type = "string"  # 指定输出类型为字符串
    
    def __init__(self, name: str, description: str):
        super().__init__()
        self.name = name
        self.description = description
        self.logger = logger.bind(tool=name)
    
    @abstractmethod
    def forward(self, query: str) -> str:
        """执行工具逻辑"""
        pass

class NetworkTool(BaseTool):
    """网络工具基类，处理代理和重试"""
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self.session = self._create_session()
    
    def _create_session(self):
        """创建带代理和重试机制的会话"""
        session = requests.Session()
        
        # 配置代理
        if config.proxy_url:
            session.proxies = {
                'http': config.proxy_url,
                'https': config.proxy_url
            }
            
            # 设置环境变量，确保子进程也能使用代理
            os.environ['http_proxy'] = config.proxy_url
            os.environ['https_proxy'] = config.proxy_url
            os.environ['HTTP_PROXY'] = config.proxy_url
            os.environ['HTTPS_PROXY'] = config.proxy_url
        
        # 配置重试
        retries = Retry(
            total=3,  # 总重试次数
            backoff_factor=1,  # 重试间隔因子
            status_forcelist=[500, 502, 503, 504],  # 需要重试的HTTP状态码
            allowed_methods=["GET", "POST"],  # 允许重试的HTTP方法
            raise_on_status=False  # 不抛出状态码异常，由调用方处理
        )
        
        # 为HTTP和HTTPS请求添加重试适配器
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=10,  # 连接池大小
            pool_maxsize=10,  # 最大连接数
            pool_block=False  # 非阻塞模式
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # 设置默认请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Connection': 'keep-alive',
        })
        
        # 禁用SSL验证警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        return session