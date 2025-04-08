import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

class ReportGenerator:
    """报告生成器，用于生成评估报告"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir (str): 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 general 目录
        self.general_dir = self.output_dir / "general"
        self.general_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, evaluation_summary: Dict[str, Any], model_name: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成评估报告
        
        Args:
            evaluation_summary (Dict[str, Any]): 评估摘要
            model_name (str): 模型名称
            questions (List[Dict[str, Any]]): 问题列表
            
        Returns:
            Dict[str, Any]: 生成的报告
        """
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建报告内容
        report = {
            "model_info": {
                "name": model_name,
                "evaluation_time": current_time,
            },
            "evaluation_summary": {
                "overall_score": evaluation_summary["overall_score"],
                "domain_scores": evaluation_summary["domain_scores"]
            },
            "domain_results": {}  # 按领域分组的结果
        }
        
        # 按领域分组问题
        for question in questions:
            domain = question.get("题目领域", "通用")
            if domain not in report["domain_results"]:
                report["domain_results"][domain] = []
            
            question_result = {
                "id": question["id"],
                "type": question.get("type", "unknown"),
                "difficulty": question.get("难度级别", "unknown"),
                "metric": question.get("测试指标", "unknown"),
                "question": question["question"],
                "standard_answer": question["answer"],
                "model_output": question.get("model_output", "")  # 添加模型输出字段
 # 添加评估结果字段
            }
            report["domain_results"][domain].append(question_result)
        
        return report
    
    def save_report(self, report: Dict[str, Any], model_name: str, dataset_name: str) -> Path:
        """
        保存报告到文件
        
        Args:
            report (Dict[str, Any]): 要保存的报告
            model_name (str): 模型名称
            dataset_name (str): 数据集名称
            
        Returns:
            Path: 保存的文件路径
        """
        # 生成文件名
        filename = f"{model_name}_{dataset_name}_evaluation.json"
        output_file = self.output_dir / filename
        
        # 保存报告
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 更新领域得分集合文件
        domains_file = self.general_dir / f"{model_name}_domains.json"
        try:
            # 尝试加载现有的领域得分集合
            with open(domains_file, "r", encoding="utf-8") as f:
                domains_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，创建新的领域得分集合
            domains_data = {
                "model_info": {
                    "name": model_name,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "domains": {}
            }
        
        # 更新每个领域的得分
        for domain, score_info in report["evaluation_summary"]["domain_scores"].items():
            if domain not in domains_data["domains"]:
                domains_data["domains"][domain] = {
                    "scores": [],
                    "average_score": 0.0,
                    "total_evaluations": 0
                }
            
            # 添加新的得分
            domains_data["domains"][domain]["scores"].append({
                "score": score_info["score"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_questions": score_info["total_questions"],
                "correct_answers": score_info["correct_answers"]
            })
            
            # 更新平均得分
            scores = [s["score"] for s in domains_data["domains"][domain]["scores"]]
            domains_data["domains"][domain]["average_score"] = sum(scores) / len(scores)
            domains_data["domains"][domain]["total_evaluations"] = len(scores)
        
        # 更新最后更新时间
        domains_data["model_info"]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存领域得分集合
        with open(domains_file, "w", encoding="utf-8") as f:
            json.dump(domains_data, f, ensure_ascii=False, indent=2)
        
        return output_file 