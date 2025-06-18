from typing import Optional, Dict, Any
import json
import re
from openai import OpenAI
from loguru import logger
from medical_smolagent import config

class LanguageDetector:
    """Language detector based on character sets with improved CJK differentiation"""
    
    # Common Chinese characters that are not used in Japanese
    CHINESE_ONLY_CHARS = r'[\u4e00-\u9fff]'
    
    # Japanese specific characters (Hiragana, Katakana, and some Japanese-specific Kanji)
    JAPANESE_HIRAGANA = r'[\u3040-\u309F]'  # Hiragana
    JAPANESE_KATAKANA = r'[\u30A0-\u30FF]'  # Katakana
    JAPANESE_PUNCTUATION = r'[\u3000-\u303F]'  # Japanese punctuation
    JAPANESE_KANA = JAPANESE_HIRAGANA + JAPANESE_KATAKANA
    
    # Korean characters
    KOREAN_CHARS = r'[\uAC00-\uD7A3]'
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detect the language of the given text with improved accuracy for CJK languages.
        
        Args:
            text: The text to analyze
            
        Returns:
            str: Detected language (Chinese, Japanese, Korean, or English)
        """
        if not text.strip():
            return "English"
            
        # Check for Japanese specific characters first
        has_hiragana = bool(re.search(cls.JAPANESE_HIRAGANA, text))
        has_katakana = bool(re.search(cls.JAPANESE_KATAKANA, text))
        has_jp_punctuation = bool(re.search(cls.JAPANESE_PUNCTUATION, text))
        
        # If text contains Hiragana or Katakana, it's definitely Japanese
        if has_hiragana or has_katakana:
            return "Japanese"
            
        # Check for Korean
        if re.search(cls.KOREAN_CHARS, text):
            return "Korean"
            
        # Check for Chinese characters
        has_chinese = bool(re.search(cls.CHINESE_ONLY_CHARS, text))
        
        # If we have Chinese characters and no Japanese indicators, it's likely Chinese
        if has_chinese and not (has_hiragana or has_katakana or has_jp_punctuation):
            # Additional check for Japanese punctuation which might indicate Japanese text
            return "Chinese"
            
        # If we have Chinese characters but also Japanese punctuation, it might be Japanese
        if has_chinese and has_jp_punctuation:
            return "Japanese"
            
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
                    
                    # 创建自定义的transport，完全绕过系统代理
                    class NoProxyTransport(httpx.HTTPTransport):
                        def handle_request(
                            self,
                            request: httpx.Request,
                        ) -> httpx.Response:
                            # 确保请求头中没有代理相关的设置
                            if 'proxy' in request.headers:
                                del request.headers['proxy']
                            if 'Proxy-Connection' in request.headers:
                                del request.headers['Proxy-Connection']
                            # 确保请求不使用代理
                            request.extensions["proxies"] = {}
                            return super().handle_request(request)
                    
                    # 创建自定义的HTTP客户端，确保不使用系统代理
                    transport = NoProxyTransport(
                        verify=False,  # 禁用SSL验证
                        retries=3,  # 重试次数
                        proxy=None  # 显式禁用代理
                    )
                    
                    # 创建HTTP客户端，确保不继承系统代理设置
                    http_client = httpx.Client(
                        timeout=30.0,
                        transport=transport,
                        trust_env=False  # 不信任环境变量中的代理设置
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
                self.logger.info(f"Detected source language: {source_lang}")
            
            # 准备翻译选项
            translation_options = {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "terms": [{"source": k, "target": v} for k, v in (terms or {}).items()]
            }
            
            # 调用翻译API
            messages = [{"role": "user", "content": text}]
            
            try:
                self.logger.info(f"Sending translation request to DashScope: {text[:100]}...")
                
                # 打印请求详情以便调试
                request_data = {
                    "model": "qwen-mt-turbo",
                    "messages": messages,
                    "extra_body": {"translation_options": translation_options}
                }
                self.logger.debug(f"Request data: {request_data}")
                
                # 发送请求
                response = self.client.chat.completions.create(
                    model="qwen-mt-turbo",
                    messages=messages,
                    extra_body={"translation_options": translation_options},
                    timeout=30.0
                )
                
                self.logger.debug(f"Raw API response: {response}")
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty or invalid response from translation API"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
                    
                translated_text = response.choices[0].message.content
                
                if not translated_text or translated_text.strip() == text.strip():
                    self.logger.warning("Translation returned the same text as input")
                
                self.logger.info(f"Successfully translated from {source_lang} to {target_lang}")
                self.logger.debug(f"Translation result: {text[:50]}... -> {translated_text[:50]}...")
                
                return translated_text
                
            except Exception as e:
                error_msg = f"Translation API call failed: {str(e)}"
                self.logger.error(error_msg, exc_info=True)  # 记录完整的堆栈跟踪
                self.logger.error(f"Request details - Text: {text}, Source: {source_lang}, Target: {target_lang}")
                
                # 尝试获取更多错误信息
                if hasattr(e, 'response'):
                    try:
                        if hasattr(e.response, 'text'):
                            self.logger.error(f"API Error Response: {e.response.text}")
                        if hasattr(e.response, 'status_code'):
                            self.logger.error(f"API Status Code: {e.response.status_code}")
                        if hasattr(e.response, 'headers'):
                            self.logger.error(f"API Response Headers: {dict(e.response.headers)}")
                    except Exception as inner_e:
                        self.logger.error(f"Error while extracting error details: {str(inner_e)}")
                
                # 返回原始文本而不是抛出异常，确保应用程序继续运行
                return f"{text}\n\n(Translation failed: {error_msg})"
            
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return f"{text}\n\n({error_msg})"
    
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