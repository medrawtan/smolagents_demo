from smolagents import Tool
from loguru import logger
from typing import List, Dict

class MedicalToolPlanner:
    """医疗工具规划器，决定使用哪些工具和调用顺序"""
    def __init__(self, tools: List[Tool]):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        self.logger = logger.bind(planner="MedicalToolPlanner")
        
        # 定义工具优先级
        self.priority_order = [
            "MedicalMCP",
            "WikipediaSearch",
            "DuckDuckGoSearch"
        ]
    
    def select_tools(self, query: str) -> List[Tool]:
        """根据查询内容选择合适的工具"""
        self.logger.info(f"为查询选择工具: {query}")
        
        # 简化逻辑：根据查询关键词选择工具
        if "计算" in query or "分析" in query:
            return [self.tool_map.get("MedicalMCP")]
        
        if "指南" in query or "定义" in query:
            return [self.tool_map.get("WikipediaSearch")]
        
        # 默认使用所有工具
        return [self.tool_map.get(name) for name in self.priority_order 
                if name in self.tool_map]
    
    def execute_plan(self, query: str, tools: List[Tool]) -> str:
        """执行工具调用计划"""
        results = []
        
        for tool in tools:
            if not tool:
                continue
                
            self.logger.info(f"调用工具: {tool.name}")
            result = tool.forward(query)
            results.append({
                "tool": tool.name,
                "result": result
            })
            
            # 如果结果足够充分，可以提前返回
            if self._is_adequate(result):
                break
        
        return self._combine_results(results)
    
    def _is_adequate(self, result: str) -> bool:
        """判断结果是否足够充分"""
        return not any(keyword in result for keyword in ["未找到相关", "错误", "不可用"])
    
    def _combine_results(self, results: List[Dict]) -> str:
        """组合多个工具的结果"""
        if not results:
            return "未找到相关信息"
            
        combined = "\n\n".join([
            f"[{item['tool']} 结果]\n{item['result']}"
            for item in results
        ])
        
        return combined