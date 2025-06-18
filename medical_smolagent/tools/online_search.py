from medical_smolagent.tools.base_tool import NetworkTool
from loguru import logger
from typing import Optional, Dict, Any
import json
import requests

class WikipediaSearchTool(NetworkTool):
    """维基百科搜索工具，用于获取医疗领域的权威信息"""
    
    def __init__(self):
        super().__init__(
            name="WikipediaSearch",
            description="使用维基百科获取医疗领域的权威信息。适用于查找疾病、药物、医疗程序等的详细说明。"
        )
        self.inputs = {
            "query": {
                "type": "string",
                "description": "The search query",
                "required": True,
                "nullable": False
            },
            "language": {
                "type": "string",
                "description": "Wikipedia language code (e.g., 'en' for English, 'zh' for Chinese)",
                "required": True,
                "nullable": False,
                "default": "en"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "required": True,
                "nullable": False,
                "default": 3
            }
        }
        self.output_type = "string"
    
    def _get_page_content(self, page_id: int, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        获取维基百科页面内容
        
        Args:
            page_id: 维基百科页面ID
            language: 语言代码
            
        Returns:
            Optional[Dict[str, Any]]: 包含页面信息的字典，如果获取失败则返回None
        """
        try:
            params = {
                "action": "query",
                "prop": "extracts|info",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "pageids": page_id,
                "format": "json",
                "redirects": 1
            }
            
            response = self.session.get(
                f"https://{language}.wikipedia.org/w/api.php",
                params=params,
                timeout=15,
                verify=False
            )
            response.raise_for_status()
            
            data = response.json()
            if "query" not in data or "pages" not in data["query"]:
                return None
                
            page = data["query"]["pages"].get(str(page_id))
            if not page:
                return None
                
            return {
                "title": page.get("title", ""),
                "extract": page.get("extract", ""),
                "url": page.get("fullurl", f"https://{language}.wikipedia.org/?curid={page_id}")
            }
            
        except Exception as e:
            self.logger.error(f"获取维基百科页面内容失败: {str(e)}")
            return None
    
    def forward(self, query: str, language: str = "en", max_results: int = 3) -> str:
        """
        执行维基百科搜索
        
        Args:
            query: 搜索关键词
            language: 维基百科语言代码，默认为英文('en')
            max_results: 最大返回结果数，默认为3
            
        Returns:
            str: 格式化的搜索结果
        """
        
        self.logger.info(f"执行维基百科搜索: {query}, 语言: {language}, 最大结果数: {max_results}")
        
        try:
            # 1. 搜索页面
            search_url = f"https://{language}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "srinfo": "totalhits",
                "srprop": "snippet|titlesnippet",
                "srwhat": "text"
            }
            
            response = self.session.get(search_url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            search_results = response.json()
            
            # 2. 处理搜索结果
            if not search_results.get("query", {}).get("search"):
                return "未找到相关结果"
                
            results = []
            search_data = search_results["query"]["search"]
            
            for i, item in enumerate(search_data[:max_results], 1):
                title = item.get("title", "")
                snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                page_id = item.get("pageid")
                
                # 3. 获取页面内容
                if page_id:
                    page_content = self._get_page_content(page_id, language)
                    if page_content and "extract" in page_content:
                        extract = page_content["extract"]
                        if extract:
                            results.append(f"{i}. {title}\n{extract}\n")
                            continue
                
                # 如果没有获取到完整内容，使用摘要
                results.append(f"{i}. {title}\n{snippet}\n")
            
            # 4. 添加来源链接
            if results:
                search_url = f"https://{language}.wikipedia.org/w/index.php?search={query.replace(' ', '+')}"
                results.append(f"\n🔗 在维基百科上查看完整结果: {search_url}")
            # 添加搜索提示
            results.append(
                "\n💡 提示: 维基百科内容由志愿者编辑，请谨慎评估信息的准确性和时效性。"
            )
            
            return "\n\n" + "\n\n".join(results)
            
        except requests.exceptions.Timeout:
            error_msg = "维基百科搜索超时，请稍后重试。"
            self.logger.error(error_msg)
            return error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"维基百科请求失败: {str(e)}"
            self.logger.error(f"{error_msg} - URL: {e.request.url if hasattr(e, 'request') else 'N/A'}")
            return error_msg
            
        except json.JSONDecodeError as e:
            error_msg = f"解析维基百科响应失败: {str(e)}"
            self.logger.error(f"{error_msg} - 响应内容: {response.text[:500] if 'response' in locals() else 'N/A'}")
            return error_msg
            
        except Exception as e:
            error_msg = f"维基百科搜索时发生未知错误: {str(e)}"
            self.logger.exception(error_msg)
            return error_msg