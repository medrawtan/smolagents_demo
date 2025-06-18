# MCP 工具管理指南

## 目录
- [查看可用工具](#查看可用工具)
- [添加新工具](#添加新工具)
- [修改现有工具](#修改现有工具)
- [删除工具](#删除工具)
- [工具开发规范](#工具开发规范)
- [常见问题](#常见问题)

## 查看可用工具

### 方法1：使用命令行工具

```bash
# 列出所有工具
python -c "from medical_smolagent.main import list_mcp_tools; list_mcp_tools()"

# 查看工具详情（包括参数）
python -c "from medical_smolagent.main import list_mcp_tools; list_mcp_tools(verbose=True)"
```

### 方法2：在代码中调用

```python
from medical_smolagent.main import list_mcp_tools

# 列出工具
list_mcp_tools()

# 查看工具详情
list_mcp_tools(verbose=True)
```

## 添加新工具

### 1. 创建新工具类

在 `tools/` 目录下创建新文件，例如 `custom_tool.py`：

```python
from smolagents import Tool

class CustomTool(Tool):
    """自定义工具的描述信息"""
    
    def __init__(self):
        super().__init__(
            name="custom_tool_name",  # 工具唯一标识
            description="工具的功能描述",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "参数1的描述"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "参数2的描述",
                        "default": 10
                    }
                },
                "required": ["param1"]  # 必填参数
            }
        )
    
    async def _arun(self, **kwargs):
        """工具的具体实现"""
        try:
            # 获取参数
            param1 = kwargs.get("param1")
            param2 = kwargs.get("param2", 10)
            
            # 实现工具逻辑
            result = f"处理结果: {param1} - {param2}"
            return result
            
        except Exception as e:
            return f"工具执行出错: {str(e)}"
```

### 2. 注册工具

在 `tools/__init__.py` 中导入并注册新工具：

```python
from .custom_tool import CustomTool

# 可用工具列表
AVAILABLE_TOOLS = [
    CustomTool(),
    # 其他工具...
]
```

## 修改现有工具

1. 在 `tools/` 目录下找到对应的工具文件
2. 修改工具类实现
3. 更新工具版本号（如果适用）
4. 更新文档字符串

## 删除工具

1. 从 `tools/__init__.py` 的 `AVAILABLE_TOOLS` 列表中移除工具
2. 删除对应的工具文件（可选）
3. 更新相关文档

## 工具开发规范

1. **命名规范**
   - 工具类名使用大驼峰命名法，如 `MedicalSearchTool`
   - 工具名称使用小写下划线命名法，如 `medical_search`
   - 参数名使用小写下划线命名法

2. **文档要求**
   - 每个工具类必须有详细的文档字符串
   - 参数必须包含类型和描述
   - 提供使用示例

3. **错误处理**
   - 捕获并处理所有可能的异常
   - 返回有意义的错误信息

4. **测试**
   - 为每个工具编写单元测试
   - 测试正常情况和异常情况

## 常见问题

### 1. 工具未显示在列表中
- 检查工具是否已正确注册到 `AVAILABLE_TOOLS`
- 检查工具类名和文件名是否正确

### 2. 参数验证失败
- 检查参数名称和类型是否与定义一致
- 确保所有必填参数都已提供

### 3. 工具执行超时
- 检查工具实现是否有长时间运行的操作
- 考虑增加超时处理

### 4. 如何调试工具
```python
# 直接调用工具方法进行测试
tool = CustomTool()
result = await tool._arun(param1="test")
print(result)
```

## 更新日志

### 2025-06-18
- 初始版本
- 添加工具管理文档
