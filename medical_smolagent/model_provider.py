from smolagents import LiteLLMModel
from loguru import logger
from medical_smolagent.config import config

class ModelProvider:
    """模型服务提供者，封装模型调用逻辑"""
    def __init__(self):
        self.model = LiteLLMModel(
            model_id=config.model_id,
            api_base=config.api_base,
            api_key=config.api_key,
            num_ctx=config.num_ctx
        )
    
    def generate(self, prompt: str) -> str:
        """生成回答"""
        try:
            response = self.model.generate(prompt)
            if hasattr(response, 'choices') and response.choices:
                if hasattr(response.choices[0], 'message'):
                    return response.choices[0].message.content
                return response.choices[0].text
            return str(response)
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return f"模型错误: {str(e)}"