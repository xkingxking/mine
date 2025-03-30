import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
    
    def generate_json_report(self, results: Dict[str, Any], filename: str):
        """
        生成JSON格式的报告
        
        Args:
            results (Dict[str, Any]): 评估结果
            filename (str): 输出文件名
        """
        output_file = self.output_dir / filename
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"JSON报告已保存到: {output_file}")
    
    def generate_excel_report(self, results: Dict[str, Any], filename: str):
        """
        生成Excel格式的报告
        
        Args:
            results (Dict[str, Any]): 评估结果
            filename (str): 输出文件名
        """
        # 提取详细结果
        detailed_results = results.get("detailed_results", [])
        
        # 创建DataFrame
        df = pd.DataFrame(detailed_results)
        
        # 添加时间戳
        df["report_time"] = datetime.now().isoformat()
        
        # 保存到Excel
        output_file = self.output_dir / filename
        df.to_excel(output_file, index=False)
        print(f"Excel报告已保存到: {output_file}")
    
    def generate_visualizations(self, results: Dict[str, Any], filename_prefix: str):
        """
        生成可视化图表
        
        Args:
            results (Dict[str, Any]): 评估结果
            filename_prefix (str): 文件名前缀
        """
        detailed_results = results.get("detailed_results", [])
        
        # 创建图表目录
        charts_dir = self.output_dir / "charts"
        charts_dir.mkdir(exist_ok=True)
        
        # 1. 安全性评分分布
        plt.figure(figsize=(10, 6))
        safety_scores = [
            r.get("evaluation_results", {}).get("safety", {}).get("safety_score", 0)
            for r in detailed_results if "error" not in r
        ]
        sns.histplot(safety_scores, bins=20)
        plt.title("安全性评分分布")
        plt.xlabel("安全性评分")
        plt.ylabel("频次")
        plt.savefig(charts_dir / f"{filename_prefix}_safety_distribution.png")
        plt.close()
        
        # 2. 准确性评分分布
        plt.figure(figsize=(10, 6))
        accuracy_scores = [
            r.get("evaluation_results", {}).get("accuracy", {}).get("accuracy_score", 0)
            for r in detailed_results if "error" not in r
        ]
        sns.histplot(accuracy_scores, bins=20)
        plt.title("准确性评分分布")
        plt.xlabel("准确性评分")
        plt.ylabel("频次")
        plt.savefig(charts_dir / f"{filename_prefix}_accuracy_distribution.png")
        plt.close()
        
        # 3. 题型分布
        plt.figure(figsize=(10, 6))
        question_types = [r.get("question_type") for r in detailed_results if "error" not in r]
        type_counts = pd.Series(question_types).value_counts()
        type_counts.plot(kind="bar")
        plt.title("题型分布")
        plt.xlabel("题型")
        plt.ylabel("数量")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(charts_dir / f"{filename_prefix}_question_types.png")
        plt.close()
        
        # 4. 领域分布
        plt.figure(figsize=(10, 6))
        domains = [r.get("domain") for r in detailed_results if "error" not in r]
        domain_counts = pd.Series(domains).value_counts()
        domain_counts.plot(kind="bar")
        plt.title("领域分布")
        plt.xlabel("领域")
        plt.ylabel("数量")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(charts_dir / f"{filename_prefix}_domains.png")
        plt.close()
    
    def generate_summary_report(self, results: Dict[str, Any], filename: str):
        """
        生成总结报告
        
        Args:
            results (Dict[str, Any]): 评估结果
            filename (str): 输出文件名
        """
        # 提取关键信息
        summary = {
            "model_info": {
                "type": results.get("model_type"),
                "name": results.get("model_name"),
                "test_time": results.get("test_time")
            },
            "test_statistics": {
                "total_questions": results.get("total_questions", 0),
                "successful_responses": results.get("successful_responses", 0),
                "failed_responses": results.get("failed_responses", 0),
                "success_rate": round(
                    results.get("successful_responses", 0) / 
                    results.get("total_questions", 1) * 100, 2
                )
            },
            "performance_metrics": {
                "average_safety_score": results.get("average_safety_score", 0),
                "average_accuracy_score": sum(
                    r.get("evaluation_results", {}).get("accuracy", {}).get("accuracy_score", 0)
                    for r in results.get("detailed_results", []) if "error" not in r
                ) / len([r for r in results.get("detailed_results", []) if "error" not in r]) if results.get("detailed_results") else 0
            },
            "usage_statistics": results.get("usage_stats", {})
        }
        
        # 保存总结报告
        output_file = self.output_dir / filename
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"总结报告已保存到: {output_file}")
    
    def generate_all_reports(self, results: Dict[str, Any], model_type: str):
        """
        生成所有类型的报告
        
        Args:
            results (Dict[str, Any]): 评估结果
            model_type (str): 模型类型
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_prefix = f"{model_type}_{timestamp}"
        
        # 生成JSON报告
        self.generate_json_report(results, f"{filename_prefix}_full.json")
        
        # 生成Excel报告
        self.generate_excel_report(results, f"{filename_prefix}_detailed.xlsx")
        
        # 生成可视化图表
        self.generate_visualizations(results, filename_prefix)
        
        # 生成总结报告
        self.generate_summary_report(results, f"{filename_prefix}_summary.json") 