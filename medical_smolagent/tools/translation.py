from typing import Optional, Dict, Any
import json
import re
from openai import OpenAI
from loguru import logger
from medical_smolagent import config

class LanguageDetector:
    """Simple language detector based on character sets"""
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect if text is Chinese, Japanese, Korean, or Western language"""
        # Check for Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return "Chinese"
            
        # Check for Japanese characters (Hiragana, Katakana, Kanji)
        if re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9faf\u3000-\u303f\uff00-\uff9f]', text):
            return "Japanese"
            
        # Check for Korean characters
        if re.search(r'[\uac00-\ud7a3]', text):
            return "Korean"
            
        # Default to English for other cases
        return "English"

class TranslationTool:
    """翻译工具，支持多种语言互译，默认翻译为中文"""
    
    def __init__(self):
        self.logger = logger
        self.client = None
        self.initialized = False
        
    def initialize(self):
        """Initialize the translation client"""
        if self.initialized:
            return
            
        try:
            if config.translation_api == "qwen" and config.dashscope_api_key:
                try:
                    import httpx
                    import os
                    
                    # 创建自定义的transport，明确设置不使用代理
                    class NoProxyTransport(httpx.HTTPTransport):
                        def handle_request(
                            self,
                            request: httpx.Request,
                        ) -> httpx.Response:
                            # 保存原始的代理设置
                            original_proxies = request.extensions.get("proxies")
                            # 强制设置不使用代理
                            request.extensions["proxies"] = {}
                            try:
                                return super().handle_request(request)
                            finally:
                                # 恢复原始的代理设置（虽然不太可能被用到）
                                if original_proxies is not None:
                                    request.extensions["proxies"] = original_proxies
                    
                    # 创建自定义的HTTP客户端
                    transport = NoProxyTransport(
                        verify=False,  # 禁用SSL验证
                        retries=3  # 重试次数
                    )
                    
                    # 创建HTTP客户端
                    http_client = httpx.Client(
                        timeout=30.0,
                        transport=transport
                    )
                    
                    # 初始化OpenAI客户端
                    self.client = OpenAI(
                        api_key=config.dashscope_api_key,
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        http_client=http_client
                    )
                    self.initialized = True
                    self.logger.info("Initialized Qwen MT translation client with direct connection (no proxy)")
                except Exception as e:
                    self.logger.error(f"Failed to initialize translation client: {e}")
                    self.initialized = False
            else:
                self.logger.warning("Qwen MT API key not configured, translation may not work")
        except Exception as e:
            self.logger.error(f"Failed to initialize translation client: {e}")
    
    def translate(
        self, 
        text: str, 
        source_lang: Optional[str] = None, 
        target_lang: str = "Chinese",
        terms: Optional[Dict[str, str]] = None
    ) -> str:
        """
        翻译文本到目标语言
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言，如果为None则自动检测
            target_lang: 目标语言，默认为中文
            terms: 术语表，用于特定术语的精确翻译
            
        Returns:
            翻译后的文本
        """
        if not text.strip():
            return text
            
        self.initialize()
        
        # 如果已经是目标语言，直接返回
        if source_lang == target_lang or (not source_lang and self._is_target_language(text, target_lang)):
            return text
        
        # 如果没有初始化客户端，返回原始文本
        if not self.initialized or not self.client:
            self.logger.warning("Translation client not initialized, returning original text")
            return text
            
        try:
            # 自动检测源语言
            if not source_lang:
                source_lang = LanguageDetector.detect_language(text)
                self.logger.debug(f"Detected source language: {source_lang}")
            
            # 准备翻译选项
            translation_options = {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "terms": [{"source": k, "target": v} for k, v in (terms or {}).items()]
            }
            
            # 调用翻译API
            messages = [{"role": "user", "content": text}]
            
            response = self.client.chat.completions.create(
                model="qwen-mt-turbo",
                messages=messages,
                extra_body={"translation_options": translation_options}
            )
            
            translated_text = response.choices[0].message.content
            self.logger.debug(f"Translated from {source_lang} to {target_lang}: {text[:50]}... -> {translated_text[:50]}...")
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation failed: {str(e)}")
            return f"{text}\n\n(Translation failed: {str(e)})"
    
    def _is_target_language(self, text: str, target_lang: str) -> bool:
        """Check if text is in the target language"""
        if target_lang == "Chinese":
            return bool(re.search(r'[\u4e00-\u9fff]', text))
        elif target_lang == "Japanese":
            return bool(re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9faf\u3000-\u303f\uff00-\uff9f]', text))
        elif target_lang == "Korean":
            return bool(re.search(r'[\uac00-\ud7a3]', text))
        # For other languages, we can't reliably detect, so assume it's not the target
        return False

# 创建全局翻译器实例
translator = TranslationTool()

def translate(
    text: str, 
    source_lang: Optional[str] = None, 
    target_lang: str = "Chinese",
    terms: Optional[Dict[str, str]] = None
) -> str:
    """
    翻译文本到目标语言（默认翻译为中文）
    
    Args:
        text: 要翻译的文本
        source_lang: 源语言，如果为None则自动检测
        target_lang: 目标语言，默认为中文
        terms: 术语表，用于特定术语的精确翻译
        
    Returns:
        翻译后的文本
    """
    return translator.translate(text, source_lang, target_lang, terms)