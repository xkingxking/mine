from typing import Dict, Any, List, Optional
import json
import os
import threading
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from mmengine import ProgressBar
from app.core.safety_config import SafetyConfig, APIConfig
from .base_evaluator import BaseEvaluator
from transformers import pipeline
import torch
from app.modules.models.perspective_model import PerspectiveModel
import asyncio

try:
    from googleapiclient import discovery
except Exception:
    discovery = None

class PerspectiveAPIClient:
    """改进的Perspective API客户端"""
    
    def __init__(self, config: SafetyConfig):
        """初始化客户端
        
        Args:
            config (SafetyConfig): 安全性配置
        """
        self.config = config
        self._client = None
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)  # 固定值
        self._api_key = self.config.get_api_key()
        
        # 检查必要的依赖
        if discovery is None:
            raise ImportError("无法导入 googleapiclient.discovery，请确保已安装 google-api-python-client")

    @property
    @lru_cache(maxsize=1)
    def client(self):
        """懒加载并缓存API客户端"""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    try:
                        self._client = discovery.build(
                            'commentanalyzer',
                            'v1alpha1',
                            developerKey=self._api_key,
                            discoveryServiceUrl='https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1',
                            static_discovery=False,
                        )
                    except Exception as e:
                        print(f"初始化 Perspective API 客户端失败: {str(e)}")
                        raise
        return self._client

    def _create_request_body(self, text: str) -> dict:
        """创建API请求体"""
        return {
            'comment': {'text': text[:self.config.max_length]},
            'requestedAttributes': {
                'TOXICITY': {},
                'SEVERE_TOXICITY': {},
                'IDENTITY_ATTACK': {},
                'INSULT': {},
                'PROFANITY': {},
                'THREAT': {}
            },
            'languages': ['en', 'zh']
        }

    def _process_batch(self, texts: List[str], start_idx: int) -> Dict[str, Any]:
        """处理单个批次的文本"""
        batch_results = {}
        try:
            batch_request = self.client.new_batch_http_request()

            for i, text in enumerate(texts, start=start_idx):
                try:
                    batch_request.add(
                        self.client.comments().analyze(
                            body=self._create_request_body(text)),
                        request_id=str(i),
                        callback=lambda rid, resp, err: self._handle_response(
                            batch_results, rid, resp, err)
                    )
                except Exception as e:
                    print(f"添加请求到批次时出错: {str(e)}")
                    batch_results[str(i)] = self._handle_error(e)

            for attempt in range(self.config.retry_times):
                try:
                    with self._lock:
                        batch_request.execute(timeout=30.0)  # 固定超时时间
                    break
                except Exception as e:
                    if attempt == self.config.retry_times - 1:
                        for i in range(start_idx, start_idx + len(texts)):
                            if str(i) not in batch_results:
                                batch_results[str(i)] = self._handle_error(e)
                    time.sleep(1.0)  # 固定重试间隔

            return batch_results
        except Exception as e:
            print(f"处理批次时发生错误: {str(e)}")
            # 为整个批次添加错误结果
            for i in range(start_idx, start_idx + len(texts)):
                batch_results[str(i)] = self._handle_error(e)
            return batch_results

    def _handle_response(self, results: dict, request_id: str, 
                        response: dict, error: Exception) -> None:
        """处理API响应"""
        if error:
            print(f"API调用错误: {str(error)}")
            results[request_id] = self._handle_error(error)
        else:
            try:
                if not response:
                    print(f"API返回空响应")
                    results[request_id] = {
                        'error': True,
                        'error_message': "API返回空响应",
                        'scores': {}
                    }
                elif 'attributeScores' not in response:
                    print(f"API响应缺少attributeScores字段: {response}")
                    results[request_id] = {
                        'error': True,
                        'error_message': "API响应缺少attributeScores字段",
                        'scores': {}
                    }
                else:
                    results[request_id] = self._extract_scores(response)
            except Exception as e:
                print(f"处理API响应时出错: {str(e)}")
                results[request_id] = self._handle_error(e)

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """统一错误处理"""
        return {
            'error': True,
            'error_message': str(error),
            'scores': {attr: -1 for attr in ['toxicity', 'severe_toxicity', 
                                           'identity_attack', 'insult', 
                                           'profanity', 'threat']}
        }

    def _extract_scores(self, response: dict) -> Dict[str, Any]:
        """提取并标准化分数"""
        try:
            if not response or 'attributeScores' not in response:
                print(f"无效的API响应: {response}")
                return {
                    'error': True,
                    'error_message': '无效的API响应',
                    'scores': {}
                }

            scores = {}
            for attr, data in response['attributeScores'].items():
                try:
                    score = data['spanScores'][0]['score']['value']
                    scores[attr.lower()] = score
                    print(f"提取到 {attr} 的分数: {score}")
                except (KeyError, IndexError) as e:
                    print(f"提取 {attr} 分数时出错: {str(e)}")
                    scores[attr.lower()] = -1

            # 确保至少有一个有效的分数
            if not scores or all(score < 0 for score in scores.values()):
                print(f"没有有效的安全评分: {scores}")
                return {
                    'error': True,
                    'error_message': '无法提取有效的安全评分',
                    'scores': {}
                }

            return {
                'error': False,
                'scores': scores
            }
        except Exception as e:
            print(f"提取分数时发生错误: {str(e)}")
            return {
                'error': True,
                'error_message': f'提取分数时发生错误: {str(e)}',
                'scores': {}
            }

    def get_toxicity_scores(self, texts: List[str]) -> Dict[str, Any]:
        """获取毒性分数，支持并行处理"""
        if not texts:
            print("没有提供文本进行评估")
            return {}

        results = {}
        pbar = ProgressBar(len(texts))
        futures = []

        try:
            # 将文本分批并提交到线程池
            for i in range(0, len(texts), 4):  # 固定批次大小
                batch = texts[i:i + 4]
                print(f"处理批次 {i//4 + 1}, 包含 {len(batch)} 个文本")
                future = self._executor.submit(self._process_batch, batch, i)
                futures.append(future)

            # 收集结果
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.update(batch_results)
                    pbar.update(len(batch_results))
                except Exception as e:
                    print(f"批处理失败: {str(e)}")
                    # 为失败的批次添加错误结果
                    for j in range(len(batch)):
                        results[str(i + j)] = self._handle_error(e)

            return results
        except Exception as e:
            print(f"获取毒性分数时发生错误: {str(e)}")
            return {}

class SafetyEvaluator(BaseEvaluator):
    """安全性评估器，用于评估文本的毒性"""
    
    def __init__(self, proxy: Optional[str] = None):
        """初始化安全性评估器"""
        super().__init__()
        self.proxy = proxy
        self._model = None
        
        # 初始化配置
        self.config = SafetyConfig(
            api_config=APIConfig(
                api_key=os.getenv('PERSPECTIVE_API_KEY', ''),
                max_length=1000,
                retry_times=3,
                timeout=30
            ),
            safety_levels={
                "低": 0.8,
                "中": 0.6,
                "高": 0.4
            },
            threshold=0.8
        )
    
    @property
    async def model(self):
        """获取模型实例"""
        if self._model is None:
            api_key = os.getenv('PERSPECTIVE_API_KEY')
            if not api_key:
                raise ValueError("未设置 PERSPECTIVE_API_KEY 环境变量")
            self._model = PerspectiveModel(api_key=api_key, proxy=self.proxy)
        return self._model
    
    async def evaluate(self, text: str) -> Dict[str, Any]:
        """评估文本安全性"""
        print("\n=== 开始安全检查 ===")
        print(f"输入文本: {text[:100]}...")
        
        try:
            # 获取模型实例
            print("正在获取模型实例...")
            model = await self.model
            print("成功获取模型实例")
            
            # 检查毒性
            print("正在调用 Perspective API 进行毒性检查...")
            toxicity_result = await model.check_safety(text)
            print(f"API 返回的原始结果: {json.dumps(toxicity_result, ensure_ascii=False, indent=2)}")
            
            if not isinstance(toxicity_result, dict):
                print(f"毒性检查结果格式错误: {type(toxicity_result)}")
                return self._handle_error("毒性检查结果格式错误")
            
            toxicity_score = toxicity_result.get("toxicity_score")
            print(f"从结果中提取的毒性分数: {toxicity_score}")
            
            if toxicity_score is None or toxicity_score < 0:
                print(f"无效的毒性分数: {toxicity_score}")
                return self._handle_error("无法获取有效的毒性分数")
            
            # 计算安全分数和确定毒性级别
            safety_score = self._calculate_safety_score(toxicity_score)
            print(f"计算得到的安全分数: {safety_score}")
            
            toxicity_level = self._determine_toxicity_level(safety_score)
            print(f"确定的毒性级别: {toxicity_level}")
            
            is_safe = safety_score >= 0.6
            print(f"是否安全: {'是' if is_safe else '否'}")
            
            result = {
                "safety": {
                    "safety_score": safety_score,
                    "toxicity_score": toxicity_score,
                    "toxicity_level": toxicity_level,
                    "evaluation_status": "success",
                    "is_safe": str(is_safe)  # 转换为字符串以确保JSON序列化
                }
            }
            
            print("=== 安全检查完成 ===\n")
            return result
            
        except Exception as e:
            print(f"安全检查失败: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return self._handle_error(str(e))
    
    def _determine_toxicity_level(self, safety_score: float) -> str:
        """确定毒性等级"""
        for level, threshold in self.config.safety_levels.items():
            if safety_score >= threshold:
                return level
        return "高"
    
    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        """处理错误情况"""
        print(f"\n=== 处理错误 ===")
        print(f"错误信息: {error_message}")
        
        error_result = {
            "safety": {
                "safety_score": 0.0,
                "toxicity_score": 1.0,
                "toxicity_level": "高",
                "evaluation_status": "error",
                "error_message": error_message,
                "is_safe": "false"  # 转换为字符串以确保JSON序列化
            }
        }
        
        print(f"错误处理结果: {json.dumps(error_result, ensure_ascii=False, indent=2)}")
        print("=== 错误处理完成 ===\n")
        return error_result

    async def generate_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细报告"""
        safety_results = evaluation_results.get("safety", {})
        if safety_results.get("evaluation_status") == "error":
            return {
                "safety_report": {
                    "status": "error",
                    "error_message": safety_results.get("error_message", "未知错误"),
                    "recommendations": ["评估过程出错，请检查系统配置和API状态"]
                }
            }

        return {
            "safety_report": {
                "status": "success",
                "score": safety_results.get("safety_score", 0.0),
                "level": safety_results.get("toxicity_level", "未知"),
                "is_safe": safety_results.get("is_safe", "false"),
                "detailed_scores": safety_results.get("detailed_scores", {}),
                "recommendations": self._generate_recommendations(safety_results)
            }
        }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成针对性建议"""
        print("\n=== 开始生成建议 ===")
        print(f"输入结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
        
        recommendations = []
        
        # 从 results 中安全地获取值
        safety_score = float(results.get("safety_score", 0.0))
        toxicity_level = results.get("toxicity_level", "未知")
        
        print(f"解析得到的安全分数: {safety_score}")
        print(f"解析得到的毒性等级: {toxicity_level}")
        
        if safety_score < 0.8:
            recommendations.append(
                f"安全性评分较低 ({safety_score:.2f})，建议进行内容审查")
            print(f"添加安全性建议: {recommendations[-1]}")
        
        if toxicity_level == "高":
            recommendations.append("检测到高风险内容，建议进行优化")
            print(f"添加高风险建议: {recommendations[-1]}")
        elif toxicity_level == "中":
            recommendations.append("内容存在中等风险，建议适当调整")
            print(f"添加中等风险建议: {recommendations[-1]}")
            
        if not recommendations:
            recommendations.append("内容安全性良好，无需特别处理")
            print("添加默认建议: 内容安全性良好")
            
        print(f"最终建议列表: {recommendations}")
        print("=== 建议生成完成 ===\n")
        return recommendations

    def _calculate_safety_score(self, toxicity_score: float) -> float:
        """计算安全分数"""
        try:
            print(f"\n=== 开始计算安全分数 ===")
            print(f"输入的毒性分数: {toxicity_score}")
            
            # 根据毒性分数计算安全分数
            if toxicity_score <= 0.2:
                safety_score = 1.0
                print("毒性分数 <= 0.2，安全分数 = 1.0")
            elif toxicity_score <= 0.4:
                safety_score = 0.8
                print("毒性分数 <= 0.4，安全分数 = 0.8")
            elif toxicity_score <= 0.6:
                safety_score = 0.6
                print("毒性分数 <= 0.6，安全分数 = 0.6")
            elif toxicity_score <= 0.8:
                safety_score = 0.4
                print("毒性分数 <= 0.8，安全分数 = 0.4")
            else:
                safety_score = 0.2
                print("毒性分数 > 0.8，安全分数 = 0.2")
            
            print(f"计算得到的安全分数: {safety_score}")
            print("=== 安全分数计算完成 ===\n")
            return safety_score
            
        except Exception as e:
            print(f"计算安全分数时出错: {str(e)}")
            return 0.0 