from datetime import datetime


class StageTracker:
    STAGES = [
        "scope_definition",
        "data_collection",
        "data_cleaning",
        "classification",
        "evidence_evaluation",
        "prd_generation",
        "test_case_generation",
        "traceability_verification",
        "result_preparation",
        "display",
    ]

    STAGE_NAMES_CN = {
        "scope_definition": "确定分析范围",
        "data_collection": "数据收集",
        "data_cleaning": "数据清洗",
        "classification": "动态分类",
        "evidence_evaluation": "证据评估",
        "prd_generation": "PRD生成",
        "test_case_generation": "测试用例生成",
        "traceability_verification": "追溯链验证",
        "result_preparation": "结果准备",
        "display": "展示",
    }

    def __init__(self):
        self.tasks = {}

    def init_task(self, task_id: str):
        self.tasks[task_id] = {}
        for stage in self.STAGES:
            self.tasks[task_id][stage] = {
                "status": "pending",
                "timestamp": None,
            }

    def update(self, task_id: str, stage: str, status: str):
        if task_id not in self.tasks:
            self.init_task(task_id)
        if stage in self.STAGES:
            self.tasks[task_id][stage] = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }

    def get_progress(self, task_id: str) -> dict:
        if task_id not in self.tasks:
            return {
                "task_id": task_id,
                "progress_percent": 0,
                "current_stage": None,
                "stages": [],
            }

        task_data = self.tasks[task_id]
        completed = 0
        total = len(self.STAGES)
        current_stage_cn = None
        stages_info = []

        for stage in self.STAGES:
            info = task_data.get(stage, {"status": "pending"})
            status = info.get("status", "pending")
            name_cn = self.STAGE_NAMES_CN.get(stage, stage)
            stages_info.append({
                "name": stage,
                "name_cn": name_cn,
                "status": status,
                "timestamp": info.get("timestamp"),
            })
            if status == "completed" or status == "failed":
                completed += 1
            if status == "in_progress":
                current_stage_cn = name_cn

        progress_percent = int(completed / total * 100) if total > 0 else 0

        return {
            "task_id": task_id,
            "progress_percent": progress_percent,
            "current_stage": current_stage_cn,
            "stages": stages_info,
        }

    def is_complete(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        task_data = self.tasks[task_id]
        for stage in self.STAGES:
            status = task_data.get(stage, {}).get("status", "pending")
            if status not in ("completed", "failed"):
                return False
        return True
