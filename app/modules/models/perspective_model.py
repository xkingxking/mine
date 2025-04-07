import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from aiohttp_socks import ProxyConnector
from .base_model import BaseModel
from app.core.config import get_model_config

class PerspectiveModel(BaseModel):
    """Perspective API 模型实现"""
    
    def __init__(self, api_key: str, model_name: str = "perspective-api", **kwargs):
        """
        初始化 Perspective 模型
        
        Args:
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
        """
        # 获取模型配置
        config = get_model_config("perspective")
        
        # 使用提供的参数覆盖配置
        api_key = api_key or config["api_key"]
        model_name = model_name or config["model_name"]
        api_base = kwargs.get("api_base", "https://commentanalyzer.googleapis.com/v1alpha1")
        
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = api_base
        self.total_calls = 0
        self.total_tokens = 0
        
        # 获取代理设置
        proxy_url = kwargs.get("proxy")
        if not proxy_url:
            print("警告：未设置代理，将尝试直接连接")
            self.connector = aiohttp.TCPConnector(ssl=False)
        else:
            print(f"使用代理: {proxy_url}")
            try:
                self.connector = ProxyConnector.from_url(
                    proxy_url,
                    ssl=False,
                    force_close=True,
                    enable_cleanup_closed=True
                )
            except Exception as e:
                print(f"代理连接器创建失败: {str(e)}")
                print("尝试使用直接连接")
                self.connector = aiohttp.TCPConnector(ssl=False)
        
        # 创建会话
        self._session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._session is None:
            self._session = aiohttp.ClientSession(connector=self.connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = None) -> str:
        """
        生成模型响应（Perspective API 不支持生成响应）
        
        Args:
            prompt (str): 用户提示词
            system_prompt (Optional[str]): 系统提示词（不使用）
            temperature (float): 温度参数（不使用）
            max_tokens (Optional[int]): 最大生成token数（不使用）
            
        Returns:
            str: 空字符串，因为 Perspective API 不支持生成响应
        """
        return ""
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        return {
            "model_name": self.model_name,
            "api_base": self.api_base,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens
        }
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """获取模型能力信息"""
        return {
            "model_type": "perspective",
            "capabilities": {
                "text_generation": False,
                "safety_check": True,
                "max_tokens": 0,
                "temperature": 0,
                "top_p": 0
            }
        }
    
    async def validate_api_key(self) -> bool:
        """验证 API 密钥是否有效"""
        try:
            async with aiohttp.ClientSession(connector=self.connector) as session:
                url = f"{self.api_base}/comments:analyze"
                params = {"key": self.api_key}
                data = {
                    "comment": {"text": "test"},
                    "requestedAttributes": {"TOXICITY": {}}
                }
                async with session.post(url, params=params, json=data) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 403:
                        print("API密钥无效")
                        return False
                    else:
                        print(f"API请求失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"API 密钥验证失败: {str(e)}")
            return False
    
    async def check_safety(self, text: str) -> Dict[str, Any]:
        """
        检查文本安全性
        
        Args:
            text (str): 待检查的文本
            
        Returns:
            Dict[str, Any]: 包含毒性分数的字典
        """
        print("\n=== 开始调用 Perspective API ===")
        print(f"待检查文本: {text[:100]}...")
        
        if not self._session:
            print("创建新的 aiohttp 会话...")
            self._session = aiohttp.ClientSession(connector=self.connector)
            
        try:
            # 构建请求URL
            url = f"{self.api_base}/comments:analyze"
            print(f"请求URL: {url}")
            
            # 构建请求体
            request_body = {
                "comment": {"text": text},
                "languages": ["zh"],
                "requestedAttributes": {
                    "TOXICITY": {}
                }
            }
            print(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
            
            # 发送请求
            print("正在发送 API 请求...")
            async with self._session.post(
                url,
                json=request_body,
                params={"key": self.api_key}
            ) as response:
                print(f"API 响应状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"API 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    toxicity = result.get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {}).get("value", 0.0)
                    print(f"提取的毒性分数: {toxicity}")
                    
                    return {
                        "toxicity_score": toxicity,
                        "evaluation_status": "success"
                    }
                else:
                    print(f"安全检查失败，状态码: {response.status}")
                    error_text = await response.text()
                    print(f"错误详情: {error_text}")
                    return {
                        "toxicity_score": 0.0,
                        "evaluation_status": "error",
                        "error_message": f"API请求失败，状态码: {response.status}"
                    }
                    
        except Exception as e:
            print(f"安全检查出错: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return {
                "toxicity_score": 0.0,
                "evaluation_status": "error",
                "error_message": str(e)
            }
    
    async def test_connection(self) -> bool:
        """测试网络连接"""
        try:
            print("正在测试网络连接...")
            async with aiohttp.ClientSession(connector=self.connector) as session:
                # 首先测试代理连接
                if isinstance(self.connector, ProxyConnector):
                    print("正在测试代理连接...")
                    try:
                        async with session.get("http://www.google.com", timeout=10) as response:
                            if response.status == 200:
                                print("代理连接测试成功")
                            else:
                                print(f"代理连接测试失败，状态码: {response.status}")
                    except Exception as e:
                        print(f"代理连接测试失败: {str(e)}")
                
                # 测试 API 连接
                print("正在测试 API 连接...")
                url = f"{self.api_base}/comments:analyze"
                params = {"key": self.api_key}
                data = {
                    "comment": {"text": "test"},
                    "requestedAttributes": {"TOXICITY": {}}
                }
                async with session.post(url, params=params, json=data, timeout=10) as response:
                    if response.status == 200:
                        print("API 连接测试成功")
                        return True
                    elif response.status == 403:
                        print("API 密钥无效")
                        return False
                    else:
                        print(f"API 连接测试失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"网络连接测试失败: {str(e)}")
            return False 