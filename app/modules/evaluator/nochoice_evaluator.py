from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import ast
import difflib
import subprocess
import os
import tempfile
import uuid
import jieba

class EnhancedEvaluator:
    def __init__(self, model_dir='models'):
        # 设置模型路径
        model_name = 'all-MiniLM-L12-v2'
        model_path = os.path.join(model_dir, 'sentence-transformers', model_name)
        
        # 模型信息
        model_info = {
            'all-MiniLM-L12-v2': {'size': '约400MB', 'description': '高性能语义相似度模型'},
            'paraphrase-MiniLM-L3-v2': {'size': '约80MB', 'description': '轻量级语义相似度模型'}
        }
        
        # 加载模型
        try:
            if os.path.exists(model_path):
                print("加载本地模型...")
                self.semantic_model = SentenceTransformer(model_path)
            else:
                print(f"开始下载模型 {model_name}...")
                print(f"模型大小: {model_info[model_name]['size']}")
                print(f"模型描述: {model_info[model_name]['description']}")
                print("下载可能需要几分钟，请耐心等待...")
                self.semantic_model = SentenceTransformer(model_name)
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                try:
                    print("正在保存模型到本地...")
                    self.semantic_model.save(model_path)
                    print(f"模型已保存到: {os.path.abspath(model_path)}")
                except Exception as e:
                    print(f"模型保存失败: {str(e)}，将继续使用内存中的模型")
        except Exception as e:
            print(f"加载 {model_name} 失败: {str(e)}")
            print("尝试使用更小的模型...")
            backup_model = 'paraphrase-MiniLM-L3-v2'
            try:
                print(f"开始下载备用模型 {backup_model}...")
                print(f"模型大小: {model_info[backup_model]['size']}")
                self.semantic_model = SentenceTransformer(backup_model)
                print("已加载更小的模型")
            except Exception as e:
                raise Exception(f"无法加载任何模型: {str(e)}")

    def evaluate_short_answer(self, model_output: str, standard_answer: str) -> tuple[float, bool]:
        """评估简答题"""
        model_output = model_output.strip('"\'')
        standard_answer = standard_answer.strip('"\'')
        
        print(f"Model Output: '{model_output}'")
        print(f"Standard Answer: '{standard_answer}'")
        
        # 语义相似度
        embeddings = self.semantic_model.encode([model_output, standard_answer])
        semantic_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # 关键词匹配
        try:
            standard_words = set(jieba.cut(standard_answer))
            model_words = set(jieba.cut(model_output))
            matched_words = len(model_words.intersection(standard_words))
            keyword_score = matched_words / len(standard_words) if standard_words else 0.0
        except Exception as e:
            print(f"关键词匹配失败: {str(e)}")
            keyword_score = 0.0
        
        # 综合评分（去掉ROUGE，重新分配权重）
        final_score = 0.7 * semantic_similarity + 0.3 * keyword_score
        is_correct = final_score >= 0.7
        
        print(f"简答题评估结果:")
        print(f"语义相似度: {semantic_similarity:.2%}")
        print(f"关键词匹配度: {keyword_score:.2%}")
        print(f"最终得分: {final_score:.2%}")
        
        return final_score, is_correct
    
    def evaluate_code(self, model_output: str, standard_answer: str) -> tuple[float, bool]:
        """评估代码题"""
        try:
            # 代码结构分析
            model_ast = ast.parse(model_output)
            standard_ast = ast.parse(standard_answer)
            
            # 代码相似度
            diff = difflib.SequenceMatcher(None, model_output, standard_answer)
            code_similarity = diff.ratio()
            
            # 运行结果对比
            model_result = self._run_code(model_output)
            standard_result = self._run_code(standard_answer)
            exec_similarity = 1.0 if model_result == standard_result else 0.5 if model_result else 0.0
            
            # 综合评分
            final_score = 0.4 * code_similarity + 0.3 * exec_similarity + 0.3 * (1 if model_ast.body else 0)
            is_correct = final_score >= 0.7
            
            print(f"代码题评估结果:")
            print(f"代码相似度: {code_similarity:.2%}")
            print(f"运行结果相似度: {exec_similarity:.2%}")
            print(f"最终得分: {final_score:.2%}")
            
            return final_score, is_correct
            
        except (SyntaxError, Exception) as e:
            print(f"代码评估错误: {str(e)}")
            return 0.0, False
    
    def evaluate_translation(self, model_output: str, standard_answer: str) -> tuple[float, bool]:
        """评估翻译题"""
        model_output = model_output.strip('"\'')
        standard_answer = standard_answer.strip('"\'')
        
        # 语义相似度
        embeddings = self.semantic_model.encode([model_output, standard_answer])
        semantic_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # 关键词匹配
        reference = set(jieba.cut(standard_answer))
        candidate = set(jieba.cut(model_output))
        matched_words = len(candidate.intersection(reference))
        keyword_score = matched_words / len(reference) if reference else 0.0
        
        # 综合评分
        final_score = 0.7 * semantic_similarity + 0.3 * keyword_score
        is_correct = final_score >= 0.7
        
        print(f"翻译题评估结果:")
        print(f"语义相似度: {semantic_similarity:.2%}")
        print(f"关键词匹配度: {keyword_score:.2%}")
        print(f"最终得分: {final_score:.2%}")
        
        return final_score, is_correct
    
    def evaluate_scenario(self, model_output: str, standard_answer: str) -> tuple[float, bool]:
        """评估场景题"""
        # 语义相似度
        embeddings = self.semantic_model.encode([model_output, standard_answer])
        semantic_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # 关键点匹配
        key_points = re.split(r'[,.!?]', standard_answer)
        matched_points = sum(1 for point in key_points if point.strip() in model_output)
        point_score = matched_points / len(key_points) if key_points else 0.0
        
        # 逻辑连贯性
        coherence_score = self._evaluate_coherence(model_output)
        
        # 综合评分
        final_score = 0.5 * semantic_similarity + 0.3 * point_score + 0.2 * coherence_score
        is_correct = final_score >= 0.7
        
        print(f"场景题评估结果:")
        print(f"语义相似度: {semantic_similarity:.2%}")
        print(f"关键点匹配度: {point_score:.2%}")
        print(f"逻辑连贯性: {coherence_score:.2%}")
        print(f"最终得分: {final_score:.2%}")
        
        return final_score, is_correct
    
    def _run_code(self, code: str) -> str:
        """运行代码并返回结果"""
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_code_{uuid.uuid4().hex}.py")
        
        try:
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(code)
            result = subprocess.check_output(
                ["python", "-u", temp_file],
                stderr=subprocess.STDOUT,
                timeout=5,
                universal_newlines=True,
                shell=False
            )
            return result.strip()
        except subprocess.TimeoutExpired:
            print("代码执行超时")
            return None
        except subprocess.CalledProcessError as e:
            print(f"代码执行错误: {e.output}")
            return None
        except Exception as e:
            print(f"执行代码时发生错误: {str(e)}")
            return None
        finally:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"删除临时文件失败: {str(e)}")
    
    def _evaluate_coherence(self, text: str) -> float:
        """逻辑连贯性评估"""
        sentences = re.split(r'[.!?]', text)
        if len(sentences) < 2:
            return 0.5
        embeddings = self.semantic_model.encode([s.strip() for s in sentences if s.strip()])
        if len(embeddings) < 2:
            return 0.5
        avg_similarity = sum(cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0] 
                            for i in range(len(embeddings)-1)) / (len(embeddings)-1)
        return avg_similarity

if __name__ == "__main__":
    evaluator = EnhancedEvaluator(model_dir=r'D:\LLM\mine\models')
    
    # 测试简答题（中文）
    model_output = "法国的首都是巴黎。"
    standard_answer = "法国的首都城市是巴黎。"
    score, is_correct = evaluator.evaluate_short_answer(model_output, standard_answer)
    print(f"得分: {score:.4f}, 是否正确: {is_correct}")
    
    # 测试代码题
    model_code = "def add(a, b):\n    return a + b\nprint(add(2, 3))"
    standard_code = "def add(x, y):\n    return x + y\nprint(add(2, 3))"
    score, is_correct = evaluator.evaluate_code(model_code, standard_code)
    print(f"得分: {score:.4f}, 是否正确: {is_correct}")