from medical_smolagent.tools.base_tool import BaseTool
from smolagents.mcp_client import MCPClient
from loguru import logger
from medical_smolagent import config

class MedicalMCPTool(BaseTool):
    """医疗领域MCP工具集成"""
    def __init__(self):
        super().__init__(
            name="MedicalMCP",
            description="使用医疗专业计算和分析工具"
        )
        self.mcp_tools = self._load_mcp_tools()
    
    def _load_mcp_tools(self):
        """加载MCP工具"""
        try:
            mcp_server_parameters = {
                "url": config.mcp_server_url,
                "transport": "streamable-http",
            }
            with MCPClient(mcp_server_parameters) as mcp_client:
                return mcp_client
        except Exception as e:
            self.logger.error(f"加载MCP工具失败: {e}")
            return []
    
    def forward(self, query: str) -> str:
        self.logger.info(f"MCP查询: {query}")
        
        if not self.mcp_tools:
            return "MCP工具不可用"
        
        # 简化示例：这里应实现MCP工具选择和调用逻辑
        # 实际应用中需要根据查询内容选择合适的MCP工具
        try:
            # 假设我们有一个名为"medical_calculator"的MCP工具
            calculator_tool = next(
                (tool for tool in self.mcp_tools if tool.name == "medical_calculator"),
                None
            )
            
            if calculator_tool:
                return calculator_tool(query)
            else:
                return "未找到合适的MCP工具"
        except Exception as e:
            self.logger.error(f"MCP工具调用失败: {e}")
            return f"MCP错误: {str(e)}"