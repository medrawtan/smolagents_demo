from typing import List
from loguru import logger
from smolagents import CodeAgent, Tool
from medical_smolagent.model_provider import ModelProvider
from medical_smolagent.planner import MedicalToolPlanner
from medical_smolagent.tools import translation

class MedicalAgent:
    def __init__(self, tools: List[Tool]):
        self.model_provider = ModelProvider()
        self.planner = MedicalToolPlanner(tools)
        self.translation_tool = translation.TranslationTool()
        
        self.agent = CodeAgent(
            tools=tools,
            model=self.model_provider.model,
            add_base_tools=True
        )
        
        self.logger = logger.bind(agent="MedicalAgent")
    
    def run(self, query: str) -> str:
        # 智能体运行逻辑...
        pass    