from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
import re
import sys

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 现在可以使用绝对导入
from app.modules.question_loader import QuestionLoader
from app.modules.evaluator.evaluation_manager import EvaluationManager
from app.modules.reporting.report_generator import ReportGenerator
from app.core.config import settings
from app.main import get_model_output

app = Flask(__name__)
# 配置 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# 定义常量
ALLOWED_DIMENSIONS = ['学科综合能力', '知识能力', '语言能力', '理解能力', '推理能力', '安全能力']
ALLOWED_DIFFICULTIES = ['easy', 'medium', 'hard']
ALLOWED_DISTRIBUTIONS = ['random', 'balanced', 'custom']

# 设置基础路径
BASE_DIR = Path(__file__).parent.parent
BASE_DATA_DIR = BASE_DIR / "data"
TRANSFORMED_DATA_DIR = BASE_DIR / "data" / "transformed"
GENERATOR_SCRIPT = BASE_DIR / "modules" / "question_generator" / "generator_test.py"
OUTPUT_FOLDER = BASE_DIR / "out" / "general"
FRONTEND_PATH = BASE_DIR.parent / "frontend"

# 确保目录存在
for directory in [BASE_DATA_DIR, TRANSFORMED_DATA_DIR, OUTPUT_FOLDER]:
    directory.mkdir(parents=True, exist_ok=True)

# 从文件名中提取时间
def extract_time_from_path(path):
    match = re.search(r'(\d{8})_(\d{6})', path)
    if match:
        date, time = match.groups()
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        hour = time[:2]
        minute = time[2:4]
        second = time[4:6]
        return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
    return datetime.now().isoformat()

# 从文件路径中提取模型名
def extract_model_from_path(path):
    filename = os.path.basename(path)
    model_match = re.match(r'^([^_]+)', filename)
    return model_match.group(1) if model_match else ''

# 获取文件元数据
def get_file_metadata(file_path):
    filename = os.path.basename(file_path)
    model_name = extract_model_from_path(filename)
    size = os.path.getsize(file_path)
    created_at = extract_time_from_path(filename)
    
    return {
        'id': os.path.splitext(filename)[0],
        'name': f"{model_name} 领域评估报告",
        'modelName': model_name,
        'type': os.path.splitext(filename)[1][1:],  # 去掉.
        'path': file_path,
        'size': size,
        'created_at': created_at
    }

# 获取文件列表
@app.route('/api/files', methods=['GET'])
def get_files():
    try:
        # 确保目录存在
        if not OUTPUT_FOLDER.exists():
            return jsonify({'error': f'输出目录不存在: {OUTPUT_FOLDER}'}), 404
        
        # 只获取目录中所有domains.json文件
        files = []
        for file_path in OUTPUT_FOLDER.glob('*domains.json'):
            files.append(get_file_metadata(str(file_path)))
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取文件内容
@app.route('/api/files/content', methods=['GET'])
def get_file_content():
    try:
        file_path = Path(request.args.get('path'))
        
        # 如果是相对路径，则转换为绝对路径
        if not file_path.is_absolute():
            file_path = OUTPUT_FOLDER / file_path.name
        
        # 确保文件存在
        if not file_path.exists():
            return jsonify({'error': f'文件不存在: {file_path}'}), 404
        
        # 读取并返回文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = json.load(f)
                
                # 如果是domain.json，重新组织数据格式以方便前端使用
                if file_path.name.endswith('domains.json'):
                    formatted_content = {
                        'model_info': content.get('model_info', {}),
                        'domains': []
                    }
                    
                    # 将domains对象转换为数组格式
                    if 'domains' in content:
                        for domain_name, domain_data in content['domains'].items():
                            domain_entry = {
                                'name': domain_name,
                                'average_score': domain_data.get('average_score', 0),
                                'total_evaluations': domain_data.get('total_evaluations', 0),
                                'scores': domain_data.get('scores', [])
                            }
                            formatted_content['domains'].append(domain_entry)
                    
                    return jsonify(formatted_content)
                
                return jsonify(content)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，则作为纯文本读取
                f.seek(0)
                content = {'text': f.read()}
        
        return jsonify(content)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 下载文件
@app.route('/api/files/download', methods=['GET'])
def download_file():
    try:
        file_path = Path(request.args.get('path'))
        
        # 如果是相对路径，则转换为绝对路径
        if not file_path.is_absolute():
            file_path = OUTPUT_FOLDER / file_path.name
        
        # 确保文件存在
        if not file_path.exists():
            return jsonify({'error': f'文件不存在: {file_path}'}), 404
        
        # 以二进制方式读取并返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 导入PDF生成模块
from app.modules.reporting.pdf_generator import generate_report_pdf

# 添加新的路由用于下载PDF格式的报告
@app.route('/api/files/download-pdf', methods=['GET'])
def download_pdf():
    try:
        file_path = request.args.get('path')
        
        # 如果是相对路径，则转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(OUTPUT_FOLDER, os.path.basename(file_path))
        
        # 确保文件存在
        if not os.path.exists(file_path):
            return jsonify({'error': f'文件不存在: {file_path}'}), 404
        
        # 读取JSON文件内容并处理为前端格式
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = json.load(f)
                formatted_data = {
                    'model_info': content.get('model_info', {}),
                    'domains': []
                }
                
                if 'domains' in content:
                    for domain_name, domain_data in content['domains'].items():
                        domain_entry = {
                            'name': domain_name,
                            'average_score': domain_data.get('average_score', 0),
                            'total_evaluations': domain_data.get('total_evaluations', 0),
                            'scores': domain_data.get('scores', [])
                        }
                        formatted_data['domains'].append(domain_entry)
            except json.JSONDecodeError:
                return jsonify({'error': '无效的JSON文件'}), 400
        
        # 提取模型名称和文件名
        model_name = extract_model_from_path(file_path)
        file_name = f"{model_name} 领域评估报告"
        
        # 生成PDF
        pdf_buffer = generate_report_pdf(formatted_data, file_name)
        
        # 返回PDF文件
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"{model_name}_domain_report.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取所有domains.json文件
@app.route('/api/files/domains', methods=['GET'])
def get_domain_files():
    try:
        dir_path = request.args.get('dirPath', OUTPUT_FOLDER)
        
        # 如果指定的目录不存在，使用默认输出目录
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            dir_path = OUTPUT_FOLDER
        
        # 确保目录存在
        if not os.path.exists(dir_path):
            return jsonify({'error': f'目录不存在: {dir_path}'}), 404
        
        # 查找所有domains.json结尾的文件
        files = []
        for file_path in glob.glob(os.path.join(dir_path, '*domains.json')):
            files.append(get_file_metadata(file_path))
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 上传文件
@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件部分'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        destination = request.form.get('destination', OUTPUT_FOLDER)
        
        # 确保目标目录存在
        if not os.path.exists(destination):
            return jsonify({'error': f'目标目录不存在: {destination}'}), 404
        
        # 保存文件
        filename = os.path.basename(file.filename)
        file_path = os.path.join(destination, filename)
        file.save(file_path)
        
        return jsonify({
            'message': '文件上传成功',
            'file': get_file_metadata(file_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 删除文件
@app.route('/api/files', methods=['DELETE'])
def delete_file():
    try:
        file_path = request.args.get('path')
        
        # 如果是相对路径，则转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(OUTPUT_FOLDER, os.path.basename(file_path))
        
        # 确保文件存在
        if not os.path.exists(file_path):
            return jsonify({'error': f'文件不存在: {file_path}'}), 404
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify({'message': '文件删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取所有模型的领域评分数据
@app.route('/api/models/domain-comparison', methods=['GET'])
def get_domain_comparison():
    try:
        # 确保目录存在
        if not OUTPUT_FOLDER.exists():
            return jsonify({'error': f'输出目录不存在: {OUTPUT_FOLDER}'}), 404
        
        # 获取所有domains.json文件
        domain_files = list(OUTPUT_FOLDER.glob('*domains.json'))
        
        # 如果没有文件，返回空结果
        if not domain_files:
            return jsonify({
                'domains': [],
                'models': [],
                'scores': {}
            })
        
        # 存储所有领域和模型
        all_domains = set()
        all_models = set()
        scores_by_model_domain = {}
        
        # 遍历所有文件，提取领域和评分数据
        for file_path in domain_files:
            model_name = extract_model_from_path(str(file_path))
            all_models.add(model_name)
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    content = json.load(f)
                    
                    # 提取领域信息
                    if 'domains' in content:
                        for domain_name, domain_data in content['domains'].items():
                            all_domains.add(domain_name)
                            
                            # 存储评分数据
                            if model_name not in scores_by_model_domain:
                                scores_by_model_domain[model_name] = {}
                            
                            scores_by_model_domain[model_name][domain_name] = {
                                'average_score': domain_data.get('average_score', 0),
                                'total_evaluations': domain_data.get('total_evaluations', 0)
                            }
                except json.JSONDecodeError:
                    continue
        
        # 整理结果
        result = {
            'domains': sorted(list(all_domains)),
            'models': sorted(list(all_models)),
            'scores': scores_by_model_domain
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_base_bank_metadata():
    """获取基础题库元数据"""
    banks = []
    for file in BASE_DATA_DIR.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                meta = data.get('metadata', {})
                
                banks.append({
                    "id": os.path.splitext(file.name)[0],
                    "name": f"{os.path.splitext(file.name)[0]}题库",
                    "total": meta.get('total', 0),
                    "dimensions": meta.get('dimensions', []),
                    "difficulty":meta.get('difficulty', []),
                    "created_at": meta.get('generated_at'),
                    "version": meta.get('version', '1.0'),
                    "is_transformed": False
                })
        except Exception as e:
            print(f"Error loading base bank {file}: {str(e)}")
    return banks

def get_transformed_bank_metadata():
    """获取变形题库元数据"""
    transformed_banks = []
    for file in TRANSFORMED_DATA_DIR.glob('*.json'):
        with open(file, 'r', encoding='utf-8') as f:
            bank = json.load(f)
            transformed_banks.append(bank)
    return transformed_banks

@app.route('/api/v1/question-banks', methods=['GET'])
def get_all_question_banks():
    """获取所有题库数据"""
    try:
        base_banks = get_base_bank_metadata()
        transformed_banks = get_transformed_bank_metadata()
        
        return jsonify({
            "baseBanks": base_banks,
            "transformedBanks": transformed_banks,
            "lastUpdated": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def validate_generation_params(data):
    """验证生成题库的参数"""
    errors = []
    dimensions = data.get('dimensions', [])
    if not dimensions:
        errors.append("至少需要指定一个维度")
    invalid_dims = [d for d in dimensions if d not in ALLOWED_DIMENSIONS]
    if invalid_dims:
        errors.append(f"包含无效维度: {', '.join(invalid_dims)}")
    difficulties = data.get('difficulties', ['medium'])
    invalid_diffs = [d for d in difficulties if d not in ALLOWED_DIFFICULTIES]
    if invalid_diffs:
        errors.append(f"包含无效难度级别: {', '.join(invalid_diffs)}")
    distribution = data.get('difficultyDistribution', 'balanced')
    if distribution not in ALLOWED_DISTRIBUTIONS:
        errors.append(f"无效的难度分布方式: {distribution}")
    if distribution == 'custom':
        easy = data.get('easyPercent', 0)
        medium = data.get('mediumPercent', 0)
        hard = data.get('hardPercent', 0)
        total = easy + medium + hard
        if total != 100:
            errors.append("自定义难度比例总和必须为100%")
    count = data.get('count', 10)
    if not isinstance(count, int) or count < 1 or count > 1000:
        errors.append("题目数量必须是1-1000之间的整数")
    name = data.get('name', '').strip()
    if not name:
        errors.append("题库名称不能为空")
    return errors

# --- Flask 路由 ---
@app.route('/api/v1/', methods=['GET'])
def read_root():
    """返回欢迎信息"""
    return jsonify({"message": "欢迎使用 LLM Evaluation 和 Question Bank API"})

@app.route('/api/v1/question-banks/<bank_id>/questions', methods=['GET'])
def get_bank_questions(bank_id):
    """获取指定题库的所有题目"""
    try:
        file_path = BASE_DATA_DIR / f"{bank_id}.json"
        is_transformed = False
        if not file_path.exists():
            file_path = TRANSFORMED_DATA_DIR / f"{bank_id}.json"
            is_transformed = True
            if not file_path.exists():
                return jsonify({"error": "题库不存在"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            questions = []
            if is_transformed:
                for item in data:
                    question = {
                        "id": item.get("original_id", "unknown"),
                        "type": item["type"],
                        "question": item["question"],
                        "answer": item["answer"],
                        "transform_method": item["transform_method"],
                        "difficulty": item["difficulty"]
                    }
                    if item["type"] == "choice":
                        options = item["options"].split("；") if "；" in item["options"] else item["options"].split(";")
                        question["choices"] = {chr(65+i): opt.strip() for i, opt in enumerate(options)}
                    questions.append(question)
            else:
                raw_questions = data.get('questions', data) if isinstance(data, dict) else data
                for item in raw_questions:
                    question = {
                        "id": item.get("id", "unknown"),
                        "type": item["type"],
                        "question": item["question"],
                        "answer": item["answer"],
                        "题目领域": item.get("题目领域", "无"),
                        "测试指标": item.get("测试指标", "无"),
                        "难度级别": item.get("难度级别", "无")
                    }
                    if item["type"] == "choice" and "choices" in item:
                        question["choices"] = item["choices"]
                    questions.append(question)
            return jsonify({"questions": questions, "total": len(questions)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/generate-question-bank', methods=['POST'])
def generate_question_bank():
    """生成新的题库"""
    try:
        data = request.json
        errors = validate_generation_params(data)
        if errors:
            return jsonify({"success": False, "errors": errors, "message": "参数验证失败"}), 400
        
        dimensions = data['dimensions']
        difficulties = data['difficulties']
        distribution = data['difficultyDistribution']
        count = data['count']
        name = data['name'].strip()
        
        safe_name = re.sub(r'[^\w\-_]', '', name.replace(' ', '_'))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = secure_filename(f"{safe_name}_{timestamp}.json")
        output_path = BASE_DATA_DIR / filename

        cmd = [
            'python', GENERATOR_SCRIPT,
            '--dimensions', ','.join(dimensions),
            '--difficulties', ','.join(difficulties),
            '--distribution', distribution,
            '--count', str(count),
            '--output', filename
        ]
        if distribution == 'custom':
            cmd.extend([
                '--easy-percent', str(data.get('easyPercent', 30)),
                '--medium-percent', str(data.get('mediumPercent', 40)),
                '--hard-percent', str(data.get('hardPercent', 30))
            ])

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(GENERATOR_SCRIPT), timeout=300)
        if result.returncode != 0:
            return jsonify({"success": False, "error": "生成题库失败", "details": result.stderr}), 500
        
        if not output_path.exists():
            return jsonify({"success": False, "error": f"生成文件不存在: {output_path}"}), 500

        with open(output_path, 'r+', encoding='utf-8') as f:
            bank_data = json.load(f)
            bank_data['metadata'] = bank_data.get('metadata', {})
            bank_data['metadata'].update({
                'name': name,
                'dimensions': dimensions,
                'difficulties': difficulties,
                'difficultyDistribution': distribution,
                'generated_at': datetime.now().isoformat(),
                'version': '2.0'
            })
            f.seek(0)
            json.dump(bank_data, f, ensure_ascii=False, indent=2)
            f.truncate()

        return jsonify({
            "success": True,
            "bankId": os.path.splitext(filename)[0],
            "bankName": name,
            "file": filename,
            "message": "题库生成成功"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "message": "生成过程中发生错误"}), 500

# --- 模型评估相关路由 ---
@app.route('/api/v1/evaluate', methods=['POST'])
async def evaluate_model():
    """评估模型接口"""
    try:
        data = request.json
        model_name = data.get('model_name')
        dataset_path = data.get('dataset_path')
        questions = data.get('questions', [])
        parameters = data.get('parameters', {})
        proxy = data.get('proxy')

        if not model_name:
            return jsonify({"error": "缺少 model_name"}), 400
        if not questions:
            return jsonify({"error": "缺少 questions"}), 400

        # 创建评估管理器
        evaluation_manager = EvaluationManager()
        
        # 处理每个问题
        for question in questions:
            try:
                # 获取模型输出
                model_output = await get_model_output(question, model_name, proxy)
                
                # 评估回答
                evaluation_results = await evaluation_manager.evaluate_response(
                    model_output=model_output,
                    standard_answer=question.get("answer"),
                    domain=question.get("题目领域", "通用"),
                    question_type=question.get("type", "choice")
                )
                
                # 打印评估结果
                print(f"\n评估结果:")
                print(f"准确性分数: {evaluation_results['accuracy']['accuracy_score']}")
                print(f"是否准确: {evaluation_results['accuracy']['is_accurate']}")
                
            except Exception as e:
                print(f"处理问题时出错: {str(e)}")
                continue
        
        # 获取评估摘要
        evaluation_summary = evaluation_manager.get_evaluation_summary()
        print("\n=== 评估摘要 ===")
        print(f"总体得分: {evaluation_summary['overall_score']:.2%}")
        for domain, scores in evaluation_summary["domain_scores"].items():
            print(f"{domain}得分: {scores['score']:.2%} ({scores['correct_answers']}/{scores['total_questions']})")
        
        # 生成报告
        report_generator = ReportGenerator(settings.OUTPUT_DIR)
        report = report_generator.generate_report(
            evaluation_summary=evaluation_summary,
            model_name=model_name,
            questions=questions
        )
        
        # 保存报告
        report_path = report_generator.save_report(report, model_name, dataset_path)
        
        return jsonify({
            "status": "success",
            "report_path": str(report_path)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/tests', methods=['GET'])
def get_tests():
    """获取测试任务列表"""
    try:
        # TODO: 实现获取测试列表的逻辑
        return jsonify({"tests": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/tests/<test_id>', methods=['GET'])
def get_test_detail(test_id):
    """获取测试详情"""
    try:
        # TODO: 实现获取测试详情的逻辑
        return jsonify({"test": {}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/tests/<test_id>/export', methods=['GET'])
def export_test_report(test_id):
    """导出测试报告"""
    try:
        # 构建报告文件路径
        report_path = Path("app/out") / f"{test_id}_evaluation.json"
        
        if not report_path.exists():
            return jsonify({"error": "报告文件不存在"}), 404
            
        # 读取并返回 JSON 报告
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
            
        return jsonify({
            "status": "success",
            "report": report_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """删除测试任务"""
    try:
        # TODO: 实现删除测试的逻辑
        return jsonify({"message": "删除成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/models', methods=['GET'])
def get_models():
    """获取模型列表"""
    try:
        # 从环境变量获取支持的模型列表
        supported_models = os.getenv('SUPPORTED_MODELS', '[]')
        models = json.loads(supported_models)
        
        # 格式化模型信息
        model_list = []
        for model_id in models:
            model_info = {
                "id": model_id,
                "name": model_id.upper(),  # 使用大写作为显示名称
                "provider": get_model_provider(model_id),  # 获取模型提供商
                "status": "available"  # 默认状态为可用
            }
            model_list.append(model_info)
        
        return jsonify({"models": model_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_model_provider(model_id):
    """根据模型ID获取提供商信息"""
    provider_map = {
        "gpt-3.5-turbo": "OpenAI",
        "gpt-4": "OpenAI",
        "claude-2": "Anthropic",
        "llama-2": "Meta",
        "chatglm3": "智谱AI",
        "deepseek": "DeepSeek",
        "gemini-pro": "Google"
    }
    return provider_map.get(model_id, "Unknown")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)