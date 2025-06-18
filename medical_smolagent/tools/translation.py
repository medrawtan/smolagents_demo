from .base_tool import NetworkTool
from loguru import logger
from medical_smolagent import config

class TranslationTool(NetworkTool):
    """翻译工具，确保回答为中文"""
    def __init__(self):
        super().__init__(
            name="Translation",
            description="将非中文内容翻译成中文"
        )
    
    def forward(self, query: str) -> str:
        # 简单判断是否需要翻译
        if any('\u4e00' <= char <= '\u9fff' for char in query):
            return query
        
        self.logger.info(f"翻译文本: {query[:50]}...")
        
        try:
            if config.translation_api == "baidu":
                return self._translate_with_baidu(query)
            else:
                # 默认使用百度翻译
                return self._translate_with_baidu(query)
        except Exception as e:
            self.logger.error(f"翻译失败: {e}")
            return query + "\n\n(翻译失败，原始内容保留)"
    
    def _translate_with_baidu(self, text: str) -> str:
        """使用百度翻译API"""
        # 实际应用中需要配置API密钥
        # 这里仅作示例，实际使用时需要替换为真实的API调用
        return f"[翻译内容]\n{text}"  # 模拟翻译结果