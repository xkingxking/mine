from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self):
        self.visualization_types = {
            "accuracy_trend": self._create_accuracy_trend,
            "safety_scores": self._create_safety_scores_chart,
            "choice_distribution": self._create_choice_distribution,
            "composite_metrics": self._create_composite_metrics_chart
        }
        
    def generate_report(self, 
                       test_results: Dict[str, Any],
                       report_type: str = "comprehensive") -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(test_results),
            "performance_metrics": self._analyze_performance(test_results),
            "safety_metrics": self._analyze_safety(test_results),
            "resource_usage": self._analyze_resources(test_results),
            "visualizations": self._generate_visualizations(test_results)
        }
        
        return report
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成总结"""
        summary = {
            "total_tests": 0,
            "success_rate": 0.0,
            "average_scores": {},
            "risk_level": "低",
            "recommendations": []
        }
        
        # 处理准确性评估结果
        if "accuracy_report" in results:
            acc_report = results["accuracy_report"]
            summary["average_scores"]["accuracy"] = acc_report["score"]
            summary["recommendations"].extend(acc_report.get("recommendations", []))
            
        # 处理安全性评估结果
        if "safety_report" in results:
            safety_report = results["safety_report"]
            if safety_report["status"] == "success":
                summary["average_scores"]["safety"] = safety_report["score"]
                summary["risk_level"] = safety_report["level"]
                summary["recommendations"].extend(safety_report.get("recommendations", []))
                
        # 处理选择题评估结果
        if "choice_report" in results:
            choice_data = results["choice_report"]
            if isinstance(choice_data, list):
                correct_count = sum(1 for item in choice_data if item["is_correct"])
                summary["total_tests"] = len(choice_data)
                summary["success_rate"] = correct_count / len(choice_data) * 100
            else:
                summary["total_tests"] = 1
                summary["success_rate"] = 100 if choice_data["is_correct"] else 0
                
        return summary
    
    def _analyze_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能指标"""
        performance = {
            "accuracy_metrics": {},
            "response_quality": {},
            "error_analysis": {}
        }
        
        if "accuracy_report" in results:
            acc_report = results["accuracy_report"]
            performance["accuracy_metrics"] = {
                "similarity_score": acc_report["score"],
                "similarity_level": acc_report["level"]
            }
            
        if "choice_report" in results:
            choice_data = results["choice_report"]
            if isinstance(choice_data, list):
                performance["response_quality"] = {
                    "correct_rate": sum(1 for item in choice_data if item["is_correct"]) / len(choice_data),
                    "average_score": sum(item["score"] for item in choice_data) / len(choice_data)
                }
            
        return performance
    
    def _analyze_safety(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析安全性指标"""
        if "safety_report" not in results:
            return {}
            
        safety_report = results["safety_report"]
        if safety_report["status"] != "success":
            return {"status": "error", "error_message": safety_report.get("error_message")}
            
        return {
            "status": "success",
            "overall_score": safety_report["score"],
            "risk_level": safety_report["level"],
            "is_safe": safety_report["is_safe"],
            "detailed_scores": safety_report["detailed_scores"]
        }
    
    def _analyze_resources(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析资源使用情况"""
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_usage": "N/A",  # 可以添加内存使用统计
            "processing_time": "N/A"  # 可以添加处理时间统计
        }
    
    def _generate_visualizations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成可视化图表"""
        visualizations = []
        for viz_type, viz_func in self.visualization_types.items():
            try:
                viz_data = viz_func(results)
                if viz_data:  # 只添加成功生成的可视化
                    visualizations.append({
                        "type": viz_type,
                        "data": viz_data
                    })
            except Exception as e:
                print(f"生成{viz_type}图表时出错: {str(e)}")
                
        return visualizations
    
    def _create_accuracy_trend(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """创建准确性趋势图"""
        if "accuracy_report" not in results:
            return None
            
        plt.figure(figsize=(10, 6))
        score = results["accuracy_report"]["score"]
        plt.bar(["相似度得分"], [score], color='skyblue')
        plt.ylim(0, 1)
        plt.title("答案相似度分析")
        
        # 保存图表
        filename = f"accuracy_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        
        return {
            "image_path": filename,
            "score": score,
            "level": results["accuracy_report"]["level"]
        }
    
    def _create_safety_scores_chart(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """创建安全性得分图表"""
        if "safety_report" not in results or results["safety_report"]["status"] != "success":
            return None
            
        detailed_scores = results["safety_report"]["detailed_scores"]
        
        plt.figure(figsize=(12, 6))
        scores = list(detailed_scores.values())
        labels = list(detailed_scores.keys())
        
        plt.bar(labels, scores, color=['red' if s > 0.5 else 'green' for s in scores])
        plt.xticks(rotation=45)
        plt.title("安全性指标分析")
        plt.ylim(0, 1)
        
        filename = f"safety_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        return {
            "image_path": filename,
            "scores": detailed_scores
        }
    
    def _create_choice_distribution(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """创建选择题分布图"""
        if "choice_report" not in results:
            return None
            
        choice_data = results["choice_report"]
        if not isinstance(choice_data, list):
            choice_data = [choice_data]
            
        correct_count = sum(1 for item in choice_data if item["is_correct"])
        incorrect_count = len(choice_data) - correct_count
        
        plt.figure(figsize=(8, 8))
        plt.pie([correct_count, incorrect_count], 
                labels=['正确', '错误'],
                colors=['green', 'red'],
                autopct='%1.1f%%')
        plt.title("选择题答案分布")
        
        filename = f"choice_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        
        return {
            "image_path": filename,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count
        }
    
    def _create_composite_metrics_chart(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """创建综合指标图表"""
        metrics = {}
        
        if "accuracy_report" in results:
            metrics["准确性"] = results["accuracy_report"]["score"]
            
        if "safety_report" in results and results["safety_report"]["status"] == "success":
            metrics["安全性"] = results["safety_report"]["score"]
            
        if "choice_report" in results:
            choice_data = results["choice_report"]
            if isinstance(choice_data, list):
                metrics["选择题正确率"] = sum(1 for item in choice_data if item["is_correct"]) / len(choice_data)
            else:
                metrics["选择题正确率"] = 1.0 if choice_data["is_correct"] else 0.0
                
        if not metrics:
            return None
            
        plt.figure(figsize=(10, 6))
        plt.bar(metrics.keys(), metrics.values(), color='skyblue')
        plt.ylim(0, 1)
        plt.title("综合评估指标")
        
        filename = f"composite_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        
        return {
            "image_path": filename,
            "metrics": metrics
        }
    
    def export_report(self, report: Dict[str, Any], format: str = "pdf") -> str:
        """导出报告"""
        if format == "html":
            return self._export_html_report(report)
        elif format == "pdf":
            return self._export_pdf_report(report)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
            
    def _export_html_report(self, report: Dict[str, Any]) -> str:
        """导出HTML格式报告"""
        summary_df = pd.DataFrame({
            "指标": ["总测试数", "成功率", "风险等级"],
            "数值": [
                report["summary"]["total_tests"],
                f"{report['summary']['success_rate']:.1f}%",
                report["summary"]["risk_level"]
            ]
        })
        
        visualizations_html = ""
        for viz in report["visualizations"]:
            if "image_path" in viz["data"]:
                visualizations_html += f"""
                <div class="visualization">
                    <h3>{viz["type"]}</h3>
                    <img src="{viz["data"]["image_path"]}" alt="{viz["type"]}">
                </div>
                """
        
        html_content = f"""
        <html>
        <head>
            <title>评估报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .visualization {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>评估报告</h1>
            <h2>总体概况</h2>
            {summary_df.to_html(index=False)}
            
            <h2>可视化分析</h2>
            {visualizations_html}
            
            <h2>改进建议</h2>
            <ul>
            {"".join(f"<li>{rec}</li>" for rec in report["summary"]["recommendations"])}
            </ul>
        </body>
        </html>
        """
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return filename
    
    
    def _export_pdf_report(self, report: Dict[str, Any]) -> str:
        """导出PDF格式报告"""
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter  # 默认A4纸尺寸 (595 x 842 点)

        # 设置字体和样式
        c.setFont("Helvetica", 12)

        # 写入标题
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 40, "评估报告")

        # 总体概况
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 80, "总体概况")
        c.setFont("Helvetica", 12)

        summary_data = report["summary"]
        c.drawString(100, height - 100, f"总测试数: {summary_data['total_tests']}")
        c.drawString(100, height - 120, f"成功率: {summary_data['success_rate']:.1f}%")
        c.drawString(100, height - 140, f"风险等级: {summary_data['risk_level']}")

        # 改进建议
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 160, "改进建议")
        c.setFont("Helvetica", 12)
        y_position = height - 180
        for rec in summary_data["recommendations"]:
            c.drawString(100, y_position, f"- {rec}")
            y_position -= 20

        # 可视化图表
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, y_position, "可视化分析")
        y_position -= 20
        for viz in report["visualizations"]:
            if "image_path" in viz["data"]:
                c.drawImage(viz["data"]["image_path"], 100, y_position, width=400, height=200)
                y_position -= 220  # 为下一个图表腾出空间

        # 保存PDF文件
        c.save()

        return filename
