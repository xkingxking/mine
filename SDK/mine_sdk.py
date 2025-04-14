import requests
import time
import os

class MineSDK:
    def __init__(self, base_url="http://localhost:5000"):
        self.session = requests.Session()
        self.base_url = base_url.rstrip("/")
        self.api_prefix = f"{self.base_url}/api/v1"
        self.raw_api = self.base_url + "/api"  # 用于 tasks 和文件接口

    # ---------- 题库 ----------
    def list_question_banks(self):
        url = f"{self.api_prefix}/question-banks"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        # 添加元数据信息
        for bank in data["baseBanks"]:
            bank_id = bank["id"]
            questions = self.preview_question_bank(bank_id)
            metadata = questions.get("metadata", {})
            bank["metadata"] = {
                "total": metadata.get("total", 0),
                "dimensions": metadata.get("dimensions", []),
                "difficulties": metadata.get("difficulties", []),
                "created_at": metadata.get("generated_at", ""),
                "version": metadata.get("version", "1.0")
            }
            
        for bank in data["transformedBanks"]:
            bank_id = bank["id"]
            questions = self.preview_question_bank(bank_id)
            metadata = questions.get("metadata", {})
            bank["metadata"] = {
                "total_transformed_versions": metadata.get("total_transformed_versions", 0),
                "transformed_at": metadata.get("transformed_at", ""),
                "source_file": metadata.get("source_file", "")
            }
            
        return data

    def create_question_bank(self, name, dimensions, difficulties, count, distribution="balanced"):
        url = f"{self.api_prefix}/generate-question-bank"
        payload = {
            "name": name,
            "dimensions": dimensions,
            "difficulties": difficulties,
            "difficultyDistribution": distribution,
            "count": count
        }
        resp = self.session.post(url, json=payload)
        return resp.json()

    def preview_question_bank(self, bank_id):
        url = f"{self.api_prefix}/question-banks/{bank_id}/questions"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def delete_question_bank(self, bank_id):
        url = f"{self.api_prefix}/question-banks/{bank_id}"
        resp = self.session.delete(url)
        resp.raise_for_status()
        return resp.json()

    # ---------- 题库变形 ----------
    def create_transform_task(self, task_name, source_file):
        url = f"{self.raw_api}/tasks"
        payload = {"name": task_name, "sourceFile": source_file}
        resp = self.session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def check_task_status(self, task_name, timeout=300):
        url = f"{self.raw_api}/tasks"
        waited = 0
        while waited < timeout:
            resp = self.session.get(url)
            resp.raise_for_status()
            task = resp.json().get("tasks", {}).get(task_name)
            if not task:
                return {"error": "任务不存在"}
            if task["status"].lower() == "completed":
                return task
            print(f"任务状态: {task['status']} ({task['progress']}%)，继续等待...")
            time.sleep(5)
            waited += 5
        return {"error": "任务超时未完成"}

    def delete_transform_task(self, task_id):
        url = f"{self.raw_api}/tasks/{task_id}"
        resp = self.session.delete(url)
        return resp.json()

    def list_all_tasks(self):
        url = f"{self.raw_api}/tasks"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    # ---------- 模型评估 ----------
    def evaluate_model(self, model_name, questions, dataset_path=""):
        url = f"{self.api_prefix}/evaluate"
        payload = {
            "model_name": model_name,
            "questions": questions,
            "dataset_path": dataset_path
        }
        resp = self.session.post(url, json=payload)
        return resp.json()

    def get_report_content(self, report_filename):
        url = f"{self.raw_api}/files/content?path={report_filename}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def download_report(self, report_filename, save_dir="./reports"):
        os.makedirs(save_dir, exist_ok=True)
        json_url = f"{self.raw_api}/files/download?path={report_filename}"
        pdf_url = f"{self.raw_api}/files/download-pdf?path={report_filename}"

        json_path = os.path.join(save_dir, report_filename)
        pdf_path = os.path.join(save_dir, report_filename.replace(".json", "_report.pdf"))

        with self.session.get(json_url) as r:
            r.raise_for_status()
            with open(json_path, "wb") as f:
                f.write(r.content)

        with self.session.get(pdf_url) as r:
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)

        return {"json": json_path, "pdf": pdf_path}

    # ---------- 模型对比 ----------
    def compare_models(self):
        url = f"{self.base_url}/api/models/domain-comparison"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()
