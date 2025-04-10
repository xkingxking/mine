from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
import re
import sys
from flask_socketio import SocketIO, emit
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import glob
from dotenv import load_dotenv
from collections import deque
import numpy as np

# 配置logger
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Additional imports from app.py
import threading
import uuid
import logging
from logging.handlers import RotatingFileHandler
import glob
from dotenv import load_dotenv
from collections import deque

# 现在可以使用绝对导入
from app.modules.question_loader import QuestionLoader
from app.modules.evaluator.evaluation_manager import EvaluationManager
from app.modules.reporting.report_generator import ReportGenerator
from app.core.config import settings
from app.main import get_model_output

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

# Load environment variables from .env file
load_dotenv()

# --- Directory configuration (from app.py) ---
APP_DIR = os.path.join(BASE_DIR)  # 现在是app/api，上层就是app目录
QUESTIONS_DIR = os.path.join(APP_DIR, 'data')  # 原题库直接使用data目录
LOGS_DIR = os.path.join(APP_DIR, 'logs', 'transformed_logs')
TASKS_LOG_FILE = os.path.join(LOGS_DIR, 'tasks.json')
TRANSFORMED_DIR = os.path.join(APP_DIR, 'data', 'transformed')
EVALUATE_DIR = os.path.join(APP_DIR, 'data', 'transformed_evaluated')

# 要排除的目录（避开这些目录中的文件作为原题库）
EXCLUDE_DIRS = ['transformed', 'transformed_evaluated']

# 确保所需目录存在
for dir_path in [LOGS_DIR, TRANSFORMED_DIR, EVALUATE_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# --- Logging configuration (from app.py) ---
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# --- App/Root Logger Configuration (for app.log and console) ---
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console Handler (for root logger)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
# Optional: Filter out Werkzeug logs from console if they are too noisy
# stream_handler.addFilter(lambda record: record.name != 'werkzeug')
root_logger.addHandler(stream_handler)

# File Handler for app.log (for root logger and app.logger)
app_log_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'app.log'), maxBytes=10000000, backupCount=5,
                                      encoding='utf-8')
app_log_handler.setFormatter(formatter)
root_logger.addHandler(app_log_handler)

app.logger.addHandler(app_log_handler)  # Add same handler to Flask's logger
app.logger.setLevel(logging.INFO)  # Ensure Flask logger level is also correct
app.logger.propagate = False  # Prevent Flask logs from being handled by root logger again

# --- Transformer Logger Configuration (for transformer.log) ---
transformer_logger = logging.getLogger('transformer')
transformer_logger.setLevel(logging.DEBUG)
transformer_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'transformer.log'), maxBytes=5000000, backupCount=3,
                                          encoding='utf-8')
transformer_handler.setFormatter(formatter)
transformer_logger.addHandler(transformer_handler)
transformer_logger.propagate = False

# --- Evaluator Logger Configuration (for evaluator.log) ---
evaluator_logger = logging.getLogger('evaluator')
evaluator_logger.setLevel(logging.DEBUG)
evaluator_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'evaluator.log'), maxBytes=5000000, backupCount=3,
                                        encoding='utf-8')
evaluator_handler.setFormatter(formatter)
evaluator_logger.addHandler(evaluator_handler)
evaluator_logger.propagate = False

# --- Werkzeug (Access Log) Configuration (for access.log) ---
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)  # Or logging.WARNING to be less verbose
access_log_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'access.log'), maxBytes=10000000, backupCount=5,
                                         encoding='utf-8')
access_log_handler.setFormatter(formatter)
werkzeug_logger.addHandler(access_log_handler)
werkzeug_logger.propagate = False

# --- Task management and concurrency (from app.py) ---
tasks = {}
MAX_CONCURRENT_TASKS = 3
running_task_count = 0
pending_queue = deque()
task_lock = threading.Lock()


def load_tasks():
    if os.path.exists(TASKS_LOG_FILE):
        with open(TASKS_LOG_FILE, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
            # 将旧版本中以UUID为键的任务转换为以任务名称为键
            converted_tasks = {}
            for task_id, task_info in tasks_data.items():
                task_name = task_info.get('name')
                if task_name:
                    # 使用任务名称作为新的键
                    task_info['id'] = task_name
                    converted_tasks[task_name] = task_info
                else:
                    # 如果没有任务名称，保持原样
                    converted_tasks[task_id] = task_info
            return converted_tasks
    return {}


def save_tasks():
    # 注意：save_tasks 现在应该在 task_lock 保护下调用，或者确保调用它的函数已经获取了锁
    with open(TASKS_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


# 加载已有任务
tasks = load_tasks()

# 应用启动时清理中断的任务 & 初始化并发计数
interrupted_count = 0
for task_id, task in list(tasks.items()):
    if task.get('status') in ['running', 'transforming', 'evaluating']:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = 'Task interrupted due to server restart.'
        tasks[task_id]['updated_at'] = datetime.now().isoformat()
        interrupted_count += 1
    elif task.get('status') == 'pending':
        pending_queue.append(task_id)

if interrupted_count > 0:
    app.logger.info(f"Marked {interrupted_count} interrupted tasks as failed.")
    save_tasks()


# 启动初始任务
def start_initial_tasks():
    global running_task_count
    with task_lock:
        while running_task_count < MAX_CONCURRENT_TASKS and pending_queue:
            task_id = pending_queue.popleft()
            if task_id in tasks and tasks[task_id]['status'] == 'pending':
                if 'source_file' in tasks[task_id]:
                    app.logger.info(f"Restarting pending task {task_id} from queue.")
                    sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
                    from transformer import TASK_STATUS
                    tasks[task_id]['status'] = TASK_STATUS['TRANSFORMING']
                    tasks[task_id]['updated_at'] = datetime.now().isoformat()
                    save_tasks()
                    running_task_count += 1
                    thread = threading.Thread(target=transform_and_evaluate_wrapper,
                                              args=(task_id, tasks[task_id]['source_file']))
                    thread.daemon = True
                    thread.start()
                else:
                    app.logger.warning(f"Pending task {task_id} in queue has no source_file, cannot restart.")
            else:
                app.logger.warning(f"Task {task_id} from queue not found or not pending.")


# 在应用启动后稍作延迟启动，确保所有路由等设置完毕
threading.Timer(2.0, start_initial_tasks).start()


# --- 清理和初始化结束 ---

# 新增辅助函数
def start_next_task():
    global running_task_count
    with task_lock:
        if running_task_count < MAX_CONCURRENT_TASKS and pending_queue:
            task_id_to_start = pending_queue.popleft()
            if task_id_to_start in tasks:
                task_info = tasks[task_id_to_start]
                if task_info['status'] == 'pending':
                    app.logger.info(f"Starting next task {task_id_to_start} from queue.")
                    running_task_count += 1
                    if 'source_file' in task_info:
                        sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
                        from transformer import TASK_STATUS
                        tasks[task_id_to_start]['status'] = TASK_STATUS['TRANSFORMING']
                        target_func = transform_and_evaluate_wrapper
                        args = (task_id_to_start, task_info['source_file'])
                    else:
                        app.logger.error(
                            f"Task {task_id_to_start} in queue is pending but has no source_file. Cannot determine start action.")
                        tasks[task_id_to_start]['status'] = 'failed'
                        tasks[task_id_to_start]['error'] = '无法确定启动类型 (无源文件)'
                        tasks[task_id_to_start]['updated_at'] = datetime.now().isoformat()
                        running_task_count -= 1
                        save_tasks()
                        threading.Timer(0.1, start_next_task).start()
                        return
                    tasks[task_id_to_start]['updated_at'] = datetime.now().isoformat()
                    save_tasks()
                    thread = threading.Thread(target=target_func, args=args)
                    thread.daemon = True
                    thread.start()
                else:
                    app.logger.warning(
                        f"Task {task_id_to_start} popped from queue but status is not pending ({task_info['status']}). Re-queuing check.")
                    threading.Timer(0.1, start_next_task).start()
            else:
                app.logger.warning(f"Task ID {task_id_to_start} from queue not found in tasks dict.")
                threading.Timer(0.1, start_next_task).start()


def transform_and_evaluate_wrapper(task_id, source_file):
    """包装器，确保任务完成后减少计数并尝试启动下一个任务"""
    global running_task_count
    try:
        transform_and_evaluate_internal(task_id, source_file)
    except Exception as e:
        app.logger.error(f"Unhandled exception in transform_and_evaluate_wrapper for task {task_id}: {e}",
                         exc_info=True)
        with task_lock:
            if task_id in tasks:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = f"Wrapper error: {str(e)}"
                tasks[task_id]['updated_at'] = datetime.now().isoformat()
                save_tasks()
    finally:
        app.logger.info(f"Task {task_id} (transform/evaluate) finished or failed.")
        with task_lock:
            running_task_count -= 1
            if running_task_count < 0:
                app.logger.warning("Running task count decreased below zero!")
                running_task_count = 0
            app.logger.info(f"Decremented running task count to: {running_task_count}")
        app.logger.info(f"Attempting to start next task after {task_id} completion.")
        start_next_task()


def transform_and_evaluate_internal(task_id, source_file):
    """实际执行变形和评估的函数"""
    try:
        sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
        from transformer import transform_questions, update_task_status as transformer_update_status, \
            TASK_STATUS as TRANSFORMER_TASK_STATUS
        from evaluator import evaluate_questions

        def update_status(status_key, message=None):
            status_value = TRANSFORMER_TASK_STATUS.get(status_key)
            if status_value:
                transformer_update_status(task_id, status_value, message)
                with task_lock:
                    if task_id in tasks:
                        tasks[task_id]['status'] = status_value
                        if message:
                            tasks[task_id]['message'] = message
                        tasks[task_id]['updated_at'] = datetime.now().isoformat()
            else:
                app.logger.error(f"Invalid status key '{status_key}' used for task {task_id}")

        source_path = os.path.join(QUESTIONS_DIR, source_file)
        transformed_path = os.path.join(TRANSFORMED_DIR, f'transformed_{task_id}.json')

        def progress_callback(progress):
            with task_lock:
                if task_id in tasks:
                    tasks[task_id]['progress'] = progress

        app.logger.info(f"Task {task_id} starting transformation.")
        transform_questions(source_path, transformed_path, progress_callback, max_idle_time=600, task_id=task_id)
        app.logger.info(f"Task {task_id} transformation finished.")

        app.logger.info(f"Task {task_id} updating status to evaluating.")
        update_status('EVALUATING')
        with task_lock:
            if task_id in tasks:
                tasks[task_id]['status'] = 'evaluating'
                tasks[task_id]['progress'] = 0
                tasks[task_id]['updated_at'] = datetime.now().isoformat()
                save_tasks()

        app.logger.info(f"Task {task_id} starting evaluation.")
        evaluate_result_path = os.path.join(EVALUATE_DIR, f'evaluate_{task_id}.json')
        evaluate_questions(source_path, transformed_path, evaluate_result_path, progress_callback, max_idle_time=600,
                           task_id=task_id)
        app.logger.info(f"Task {task_id} evaluation finished.")

        app.logger.info(f"Task {task_id} updating status to completed.")
        update_status('COMPLETED')
        with task_lock:
            if task_id in tasks:
                tasks[task_id]['progress'] = 100
                tasks[task_id]['completed_at'] = datetime.now().isoformat()
                tasks[task_id]['transformed_file'] = f'transformed_{task_id}.json'
                tasks[task_id]['evaluate_file'] = f'evaluate_{task_id}.json'
                tasks[task_id]['error'] = None
                tasks[task_id]['message'] = None
                save_tasks()
    except Exception as e:
        app.logger.error(f"Task {task_id} failed during transform/evaluate: {str(e)}", exc_info=True)
        sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
        from transformer import update_task_status as transformer_update_status, TASK_STATUS as TRANSFORMER_TASK_STATUS
        transformer_update_status(task_id, TRANSFORMER_TASK_STATUS['FAILED'], str(e))
        with task_lock:
            if task_id in tasks:
                tasks[task_id]['status'] = TRANSFORMER_TASK_STATUS['FAILED']
                tasks[task_id]['error'] = str(e)
                tasks[task_id]['updated_at'] = datetime.now().isoformat()
        # save_tasks() 让 transformer 的 update 函数处理持久化


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
        'type': os.path.splitext(filename)[1][1:],
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
                                'average_score': content['domains'][domain_name].get('average_score', 0),
                                'total_evaluations': content['domains'][domain_name].get('total_evaluations', 0),
                                'scores': content['domains'][domain_name].get('scores', [])
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
            as_attachment=False,
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
                    "difficulty": meta.get('difficulty', []),
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
    
    # 读取任务信息
    tasks_data = {}
    tasks_log_path = os.path.join(APP_DIR, 'logs/transformed_logs/tasks.json')
    if os.path.exists(tasks_log_path):
        try:
            with open(tasks_log_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
        except Exception as e:
            app.logger.error(f"读取tasks.json文件失败: {e}")
    
    # 创建transformed文件名到任务名称的映射
    file_to_task_map = {}
    for task_id, task_info in tasks_data.items():
        if 'transformed_file' in task_info:
            file_to_task_map[task_info['transformed_file']] = task_id
    
    # 读取变形题库文件
    for file in TRANSFORMED_DATA_DIR.glob('*.json'):
        filename = file.name
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 提取必要的元数据，只保留最基本信息
                bank = {
                    "id": os.path.splitext(filename)[0],  # 使用文件名作为ID
                    "metadata": {
                        "total_transformed_versions": data.get("metadata", {}).get("total_transformed_versions", 0)
                    },
                    "transformed_at": data.get("transformed_at", datetime.now().isoformat()),
                    "source_file": data.get("source_file", "unknown.json"),
                    "questions": data.get("questions", [])
                }
                
                # 添加任务名称信息
                task_name = None
                if filename in file_to_task_map:
                    task_name = file_to_task_map[filename]
                elif filename.startswith('transformed_'):
                    # 尝试从文件名提取任务名
                    potential_task_id = filename.replace('transformed_', '').replace('.json', '')
                    if potential_task_id in tasks_data:
                        task_name = potential_task_id
                
                # 添加任务名称到bank中
                if task_name:
                    bank['taskName'] = task_name
                
                transformed_banks.append(bank)
        except Exception as e:
            app.logger.error(f"无法加载变形题库文件 {filename}: {str(e)}")
            
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
                # 处理变形题库的新格式
                if 'questions' in data and isinstance(data['questions'], list):
                    # 新格式：包含原始问题和变形版本
                    total_original = len(data['questions'])
                    total_transformed = 0
                    unique_questions = set()  # 用于跟踪不重复题目
                    
                    for question_obj in data['questions']:
                        original_question = question_obj.get('original_question', {})
                        transformed_versions = question_obj.get('transformed_versions', [])
                        
                        # 计算总变形版本数
                        total_transformed += len(transformed_versions)
                        
                        # 为原始题目创建一个唯一标识符
                        original_id = original_question.get('id', '')
                        if original_id and original_id not in unique_questions:
                            unique_questions.add(original_id)
                        
                        # 添加变形版本题目
                        for i, version in enumerate(transformed_versions):
                            # 生成一个确保唯一的题目ID，结合原始ID、变形方法和序号
                            unique_id = f"{version.get('original_id', original_question.get('id', 'unknown'))}_{version.get('transform_method', '').replace('（','').replace('）','')[:4]}_{i+1}"
                            
                            transformed_question = {
                                "id": unique_id, # 使用唯一ID而不是原始ID
                                "original_id": version.get("original_id", original_question.get("id", "unknown")),
                                "type": version.get("type", original_question.get("type", "unknown")),
                                "question": version.get("question", ""),
                                "answer": version.get("answer", ""),
                                "transform_method": version.get("transform_method", "未知"),
                                "difficulty": version.get("difficulty", "中等"),
                                "title": f"{original_question.get('id', 'unknown')} - ({version.get('transform_method', '未知变形')})" # 添加标题字段用于显示
                            }
                            
                            # 处理选项
                            if version.get("type") == "choice" and version.get("options"):
                                if isinstance(version["options"], dict):
                                    transformed_question["choices"] = version["options"]
                                elif isinstance(version["options"], str):
                                    options = version["options"].split("；") if "；" in version["options"] else version["options"].split(";")
                                    transformed_question["choices"] = {chr(65 + i): opt.strip() for i, opt in enumerate(options)}
                            
                            questions.append(transformed_question)
                    
                    # 更新元数据
                    if 'metadata' not in data:
                        data['metadata'] = {}
                    if 'total_transformed_versions' not in data['metadata']:
                        data['metadata']['total_transformed_versions'] = total_transformed
                else:
                    # 老式变形题库直接包含题目列表
                    for i, item in enumerate(data):
                        # 为老式变形题库也创建唯一ID
                        unique_id = f"{item.get('original_id', 'unknown')}_{item.get('transform_method', '').replace('（','').replace('）','')[:4]}_{i+1}"
                        
                        question = {
                            "id": unique_id, # 使用唯一ID
                            "original_id": item.get("original_id", "unknown"),
                            "type": item["type"],
                            "question": item["question"],
                            "answer": item["answer"],
                            "transform_method": item["transform_method"],
                            "difficulty": item["difficulty"],
                            "title": f"{item.get('original_id', 'unknown')} - ({item.get('transform_method', '未知变形')})" # 标题显示方式一致
                        }
                        if item["type"] == "choice":
                            options = item["options"].split("；") if "；" in item["options"] else item["options"].split(";")
                            question["choices"] = {chr(65 + i): opt.strip() for i, opt in enumerate(options)}
                        questions.append(question)
            else:
                # 处理原始题库
                raw_questions = data.get('questions', data) if isinstance(data, dict) else data
                for item in raw_questions:
                    question = {
                        "id": item.get("id", "unknown"),
                        "type": item["type"],
                        "question": item["question"],
                        "answer": item["answer"],
                        "题目领域": item.get("题目领域", "无"),
                        "测试指标": item.get("测试指标", "无"),
                        "难度级别": item.get("难度级别", "无"),
                        "title": f"{item.get('id', 'unknown')} - {item.get('question', '')[:20]}..." # 为原题库添加标题字段
                    }
                    if item.get("choices"):
                        question["choices"] = item["choices"]
                    questions.append(question)
            # 添加元数据信息到响应中
            metadata = {}
            if is_transformed:
                # 处理新格式的简化元数据
                metadata = {
                    "total_transformed_versions": data.get("metadata", {}).get("total_transformed_versions", len(questions)),
                    "transformed_at": data.get("transformed_at", ""),
                    "source_file": data.get("source_file", "")
                }
            else:
                # 处理原始题库元数据
                metadata = data.get("metadata", {})
                
            return jsonify({
                "questions": questions, 
                "total": len(questions),
                "metadata": metadata
            })
    except Exception as e:
        app.logger.error(f"获取题库题目时出错: {str(e)}", exc_info=True)
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
    try:
        data = request.json
        model_name = data.get('model_name')
        dataset_path = data.get('dataset_path')
        questions = data.get('questions', [])
        parameters = data.get('parameters', {})
        proxy = data.get('proxy')
        
        if not model_name or not questions:
            return jsonify({"error": "缺少必要参数"}), 400
            
        evaluation_manager = EvaluationManager()
        logger.info(f"开始评估，共 {len(questions)} 个问题")
        
        for question in questions:
            try:
                model_output = await get_model_output(question, model_name, proxy)
                logger.info(f"处理问题: {question.get('id', 'unknown')}")
                
                evaluation_results = await evaluate_response(
                    model_output=model_output,
                    standard_answer=question.get("answer"),
                    difficulty=question.get("难度级别", "中等"),
                    domain=question.get("题目领域", "通用"),
                    question_type=question.get("type", "choice")
                )
                
                logger.info(f"问题评估结果: {evaluation_results}")
                
                # 确保发送到前端的数据已经转换
                socketio.emit('evaluation_result', {
                    'question_id': question.get('id', 'unknown'),
                    'question': question.get('question', ''),
                    'model_output': model_output,
                    'accuracy_score': float(evaluation_results['accuracy']['accuracy_score']),
                    'is_accurate': bool(evaluation_results['accuracy']['is_accurate'])
                })
                
            except Exception as e:
                logger.error(f"处理问题时出错: {str(e)}")
                continue
                
        # 获取评估摘要
        evaluation_summary = evaluation_manager.get_evaluation_summary()
        logger.info(f"评估摘要: {evaluation_summary}")
        
        # 生成报告
        report_generator = ReportGenerator(settings.OUTPUT_DIR)
        report = report_generator.generate_report(
            evaluation_summary=evaluation_summary,
            model_name=model_name,
            questions=questions
        )
        
        # 保存报告
        report_path = report_generator.save_report(report, model_name, dataset_path)
        logger.info(f"报告已保存: {report_path}")
        
        return jsonify({
            "status": "success",
            "report_path": str(report_path)
        })
        
    except Exception as e:
        logger.error(f"评估过程出错: {str(e)}")
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
                "name": model_id.upper(),
                "provider": get_model_provider(model_id),
                "status": "available"
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


# --- Additional API endpoints (from app.py) ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # 支持状态筛选和搜索
    status = request.args.get('status')
    search = request.args.get('search', '').lower()
    filtered_tasks = tasks.copy()
    if status:
        filtered_tasks = {k: v for k, v in filtered_tasks.items() if v['status'] == status}
    if search:
        filtered_tasks = {k: v for k, v in filtered_tasks.items() if
                          search in v['name'].lower() or search in v['source_file'].lower()}
    return jsonify({
        'status': 'success',
        'tasks': filtered_tasks
    })


@app.route('/api/tasks', methods=['POST'])
def create_task():
    global running_task_count
    try:
        data = request.json
        task_name = data.get('name')
        source_file = data.get('sourceFile')
        if not task_name or not source_file:
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        # 检查文件是否存在，并确保不是从exclude目录中获取文件
        if any(source_file.startswith(exclude_dir + '/') or source_file.startswith(exclude_dir + '\\') for exclude_dir
               in EXCLUDE_DIRS):
            return jsonify({'status': 'error', 'message': f'无效的原题库文件: {source_file}'}), 400
        source_path = os.path.join(QUESTIONS_DIR, source_file)
        if not os.path.exists(source_path) or os.path.isdir(source_path):
            return jsonify({'status': 'error', 'message': f'源文件不存在或路径是目录: {source_file}'}), 404
        with task_lock:
            # 检查任务名是否重复
            task_id = task_name  # 使用任务名称作为ID
            if task_id in tasks:
                return jsonify({'status': 'error', 'message': '任务名称已存在'}), 400
            # 创建新任务
            task = {
                'id': task_id,
                'name': task_name,
                'source_file': source_file,
                'created_at': datetime.now().isoformat(),
                'status': 'pending',
                'progress': 0,
                'ip_address': request.remote_addr,
                'updated_at': datetime.now().isoformat()
            }
            tasks[task_id] = task
            app.logger.info(f"Created task {task_id} with status 'pending'.")
            # 决定是立即启动还是加入队列
            if running_task_count < MAX_CONCURRENT_TASKS:
                running_task_count += 1
                sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
                from transformer import TASK_STATUS
                tasks[task_id]['status'] = TASK_STATUS['TRANSFORMING']
                tasks[task_id]['updated_at'] = datetime.now().isoformat()
                save_tasks()
                app.logger.info(f"Starting task {task_id} immediately. Running count: {running_task_count}")
                thread = threading.Thread(
                    target=transform_and_evaluate_wrapper,
                    args=(task_id, source_file)
                )
                thread.daemon = True
                thread.start()
            else:
                pending_queue.append(task_id)
                save_tasks()
                app.logger.info(
                    f"Queuing task {task_id}. Running count: {running_task_count}, Queue size: {len(pending_queue)}")
        return jsonify({
            'status': 'success',
            'task': tasks[task_id]
        })
    except Exception as e:
        app.logger.error(f'Create task failed: {str(e)}', exc_info=True)
        return jsonify({'status': 'error', 'message': f"创建任务时出错: {str(e)}"}), 500


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task_endpoint(task_id):
    app.logger.info(f"接收到删除任务请求: {task_id}")
    global tasks, running_task_count, pending_queue
    with task_lock:
        if task_id in tasks:
            task_info = tasks[task_id]
            original_status = task_info['status']
            try:
                # 尝试删除相关文件
                transformed_file = task_info.get('transformed_file')
                if transformed_file:
                    transformed_path = os.path.join(TRANSFORMED_DIR, transformed_file)
                    if os.path.exists(transformed_path):
                        os.remove(transformed_path)
                        app.logger.info(f"已删除变形文件: {transformed_path}")
                evaluate_file = task_info.get('evaluate_file')
                if evaluate_file:
                    evaluate_path = os.path.join(EVALUATE_DIR, evaluate_file)
                    if os.path.exists(evaluate_path):
                        os.remove(evaluate_path)
                        app.logger.info(f"已删除评估文件: {evaluate_path}")
                # 从任务字典中删除
                del tasks[task_id]
                app.logger.info(f"已从内存中删除任务 {task_id}")
                # 如果任务在队列中，尝试从队列中移除
                try:
                    pending_queue.remove(task_id)
                    app.logger.info(f"已从等待队列中删除任务 {task_id}")
                except ValueError:
                    pass
                # 如果任务正在运行，不减少 running_task_count（线程结束时会处理计数器）
                save_tasks()
                app.logger.info(f"Attempting to start next task after deleting {task_id}.")
                threading.Timer(0.1, start_next_task).start()
                return jsonify({'status': 'success', 'message': '任务删除成功'})
            except Exception as e:
                app.logger.error(f"删除任务 {task_id} 时出错: {e}", exc_info=True)
                return jsonify({'status': 'error', 'message': f'删除任务时出错: {e}'}), 500
        else:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404


@app.route('/api/tasks/<task_id>/retry', methods=['POST'])
def retry_task_endpoint(task_id):
    global running_task_count
    app.logger.info(f"接收到重试任务请求: {task_id}")
    if task_id not in tasks:
        return jsonify({'status': 'error', 'message': '任务不存在'}), 404
    task_info = tasks[task_id]
    sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
    from transformer import retry_task
    retry_result = retry_task(task_id)
    if retry_result["status"] == "error":
        app.logger.error(f"任务 {task_id} 重试失败: {retry_result['message']}")
        return jsonify({'status': 'error', 'message': retry_result['message']}), 400
    source_file = retry_result.get("source_file")
    if not source_file:
        app.logger.error(f"任务 {task_id} 没有源文件信息")
        return jsonify({'status': 'error', 'message': '任务缺少源文件信息'}), 400
    with task_lock:
        if running_task_count < MAX_CONCURRENT_TASKS:
            app.logger.info(f"立即启动重试任务 {task_id}")
            running_task_count += 1
            sys.path.append(os.path.join(APP_DIR, 'modules', 'transformer'))
            from transformer import TASK_STATUS
            tasks[task_id]['status'] = TASK_STATUS['TRANSFORMING']
            tasks[task_id]['updated_at'] = datetime.now().isoformat()
            tasks[task_id]['error'] = None
            save_tasks()
            thread = threading.Thread(
                target=transform_and_evaluate_wrapper,
                args=(task_id, source_file)
            )
            thread.daemon = True
            thread.start()
        else:
            app.logger.info(f"任务 {task_id} 加入等待队列。当前运行任务数: {running_task_count}")
            pending_queue.append(task_id)
            save_tasks()


@app.route('/api/tasks/<task_id>/transformed', methods=['GET'])
def get_transformed_result(task_id):
    app.logger.info(f"请求获取任务 {task_id} 的变形结果")
    if task_id not in tasks:
        return jsonify({'status': 'error', 'message': '任务不存在'}), 404
    task_info = tasks[task_id]
    transformed_file = task_info.get('transformed_file')
    if not transformed_file:
        return jsonify({'status': 'error', 'message': '任务尚未生成变形结果文件或变形失败'}), 404
    file_path = os.path.join(TRANSFORMED_DIR, transformed_file)
    if not os.path.exists(file_path):
        app.logger.error(f"变形结果文件丢失: {file_path}")
        return jsonify({'status': 'error', 'message': '变形结果文件丢失'}), 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        app.logger.error(f"读取变形结果文件 {file_path} 失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': '读取变形结果文件失败'}), 500


@app.route('/api/tasks/<task_id>/evaluation', methods=['GET'])
def get_evaluation_result(task_id):
    app.logger.info(f"请求获取任务 {task_id} 的评估结果")
    if task_id not in tasks:
        return jsonify({'status': 'error', 'message': '任务不存在'}), 404
    task_info = tasks[task_id]
    evaluate_file = task_info.get('evaluate_file')
    if not evaluate_file:
        return jsonify({'status': 'error', 'message': '任务尚未生成评估结果文件或评估失败'}), 404
    file_path = os.path.join(EVALUATE_DIR, evaluate_file)
    if not os.path.exists(file_path):
        app.logger.error(f"评估结果文件丢失: {file_path}")
        return jsonify({'status': 'error', 'message': '评估结果文件丢失'}), 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        app.logger.error(f"读取评估结果文件 {file_path} 失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': '读取评估结果文件失败'}), 500


@app.route('/api/questions', methods=['GET'])
def get_question_files():
    try:
        files = []
        for f in os.listdir(QUESTIONS_DIR):
            if f.endswith('.json') and not any(
                    f.startswith(exclude_dir + '/') or f.startswith(exclude_dir + '\\') for exclude_dir in
                    EXCLUDE_DIRS):
                if not os.path.isdir(os.path.join(QUESTIONS_DIR, f)):
                    files.append(f)
        return jsonify({'status': 'success', 'files': files})
    except Exception as e:
        app.logger.error(f"获取题库列表失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/questions/<filename>', methods=['GET'])
def get_question_details(filename):
    try:
        file_path = os.path.join(QUESTIONS_DIR, filename)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return jsonify({'status': 'error', 'message': '文件不存在或路径是目录'}), 404
        if any(filename.startswith(exclude_dir + '/') or filename.startswith(exclude_dir + '\\') for exclude_dir in
               EXCLUDE_DIRS):
            return jsonify({'status': 'error', 'message': '无效的原题库文件'}), 400
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        metadata = data.get('metadata', {})
        distribution = metadata.get('distribution', {})
        return jsonify({
            'status': 'success',
            'questionCount': metadata.get('total', 0),
            'dimensionDistribution': {
                dim: len([q for q in data.get('questions', []) if q.get('题目领域') == dim])
                for dim in distribution.get('dimensions', [])
            },
            'difficultyDistribution': distribution.get('difficulty', {}),
            'typeDistribution': distribution.get('types', {})
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/questions/<filename>/preview', methods=['GET'])
def get_question_preview(filename):
    try:
        file_path = os.path.join(QUESTIONS_DIR, filename)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return jsonify({'status': 'error', 'message': '文件不存在或路径是目录'}), 404
        if any(filename.startswith(exclude_dir + '/') or filename.startswith(exclude_dir + '\\') for exclude_dir in
               EXCLUDE_DIRS):
            return jsonify({'status': 'error', 'message': '无效的原题库文件'}), 400
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'status': 'success', 'questions': data.get('questions', [])})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/question_banks', methods=['GET'])
def get_question_banks():
    try:
        files = []
        for f in os.listdir(QUESTIONS_DIR):
            if f.endswith('.json') and not any(
                    f.startswith(exclude_dir + '/') or f.startswith(exclude_dir + '\\') for exclude_dir in
                    EXCLUDE_DIRS):
                if not os.path.isdir(os.path.join(QUESTIONS_DIR, f)):
                    files.append(f)
        return jsonify({'status': 'success', 'files': files})
    except Exception as e:
        app.logger.error(f"Error listing question banks: {e}")
        return jsonify({'status': 'error', 'message': '无法获取题库列表'}), 500


@app.route('/api/question_banks/<path:filename>/details', methods=['GET'])
def get_question_bank_details(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'status': 'error', 'message': '无效的文件名'}), 400
    if any(filename.startswith(exclude_dir + '/') or filename.startswith(exclude_dir + '\\') for exclude_dir in
           EXCLUDE_DIRS):
        return jsonify({'status': 'error', 'message': '无效的原题库文件'}), 400
    filepath = os.path.join(QUESTIONS_DIR, filename)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        app.logger.warning(f"Question bank details requested for non-existent file: {filename}")
        return jsonify({'status': 'error', 'message': '文件未找到'}), 404
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        metadata = data.get('metadata', {})
        app.logger.info(f"Successfully retrieved metadata for {filename}")
        return jsonify({'status': 'success', 'metadata': metadata})
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding JSON for file: {filename}")
        return jsonify({'status': 'error', 'message': '无法解析文件内容 (JSON格式错误)'}), 500
    except Exception as e:
        app.logger.error(f"Error reading file details for {filename}: {e}")
        return jsonify({'status': 'error', 'message': '读取文件详情时发生错误'}), 500


@app.route('/results/<path:filename>')
def serve_result_file(filename):
    if 'transformed' in filename:
        directory = TRANSFORMED_DIR
    elif 'evaluate' in filename:
        directory = EVALUATE_DIR
    else:
        return jsonify({'status': 'error', 'message': '无效的文件路径'}), 400
    secure_path = os.path.normpath(os.path.join(directory, filename))
    if not secure_path.startswith(directory):
        return jsonify({'status': 'error', 'message': '访问被拒绝'}), 403
    try:
        return send_from_directory(directory, filename, as_attachment=False)
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': '文件未找到'}), 404


@socketio.on('connect')
def handle_connect():
    logging.info('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('客户端已断开连接')


def evaluate_response(model_output, standard_answer, difficulty="中等", domain="通用", question_type="choice"):
    try:
        evaluation_manager = EvaluationManager()
        result = evaluation_manager.evaluate_response(
            model_output=model_output,
            standard_answer=standard_answer,
            difficulty=difficulty,
            domain=domain,
            question_type=question_type
        )
        
        # 转换所有数值类型
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (np.float32, np.float64)):
                    result[key] = float(value)
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (np.float32, np.float64)):
                            result[key][sub_key] = float(sub_value)
                        elif isinstance(sub_value, dict):
                            for sub_sub_key, sub_sub_value in sub_value.items():
                                if isinstance(sub_sub_value, (np.float32, np.float64)):
                                    result[key][sub_key][sub_sub_key] = float(sub_sub_value)
        
        return result
    except Exception as e:
        logger.error(f"处理问题时出错: {str(e)}")
        raise


if __name__ == '__main__':
    # Ensure directories exist (from app.py)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(QUESTIONS_DIR, exist_ok=True)
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    os.makedirs(EVALUATE_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
