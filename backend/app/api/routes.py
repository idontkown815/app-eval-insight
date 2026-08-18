import io
import json
import uuid
import threading
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    ValidateLinkRequest,
    ValidateLinkResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    ImportResponse,
    HealthResponse,
)
from app.collector.link_parser import LinkParser
from app.collector.file_importer import FileImporter
from app.pipeline.orchestrator import PipelineOrchestrator
from app import config


router = APIRouter(prefix="/api")

tasks_results: dict = {}
pipeline = PipelineOrchestrator()
tracker = pipeline.tracker
link_parser = LinkParser()
file_importer = FileImporter()


def _run_pipeline(task_id: str, bundle_id: str, user_goal: str, filters: dict, app_info: dict = None):
    try:
        tracker.init_task(task_id)
        result = pipeline.run(task_id, bundle_id, user_goal, filters, app_info)
        tasks_results[task_id] = result
    except Exception as e:
        tasks_results[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }


@router.post("/validate-link", response_model=ValidateLinkResponse)
async def validate_link(request: ValidateLinkRequest):
    try:
        parsed = link_parser.parse(request.url)
        bundle_id = parsed.get("bundle_id")
        app_info = link_parser.fetch_app_info(bundle_id)
        return ValidateLinkResponse(
            valid=True,
            bundle_id=bundle_id,
            app_info=app_info,
            error=None,
        )
    except ValueError as e:
        return ValidateLinkResponse(
            valid=False,
            bundle_id=None,
            app_info=None,
            error=str(e),
        )
    except Exception as e:
        return ValidateLinkResponse(
            valid=False,
            bundle_id=None,
            app_info=None,
            error=f"验证失败: {str(e)}",
        )


@router.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    task_id = str(uuid.uuid4())
    filters = request.config or {}
    app_info = {}
    try:
        app_info = link_parser.fetch_app_info(request.bundle_id)
    except Exception:
        pass

    tasks_results[task_id] = {
        "task_id": task_id,
        "status": "running",
    }

    thread = threading.Thread(
        target=_run_pipeline,
        args=(task_id, request.bundle_id, request.user_goal, filters, app_info),
        daemon=True,
    )
    thread.start()

    return CreateTaskResponse(
        task_id=task_id,
        status="running",
    )


@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    progress = tracker.get_progress(task_id)
    result = tasks_results.get(task_id, {})
    is_using_cache = result.get("data_source") == "cache"
    status = "running"
    if result.get("status") == "completed":
        status = "completed"
    elif result.get("status") == "failed":
        status = "failed"
    else:
        if tracker.is_complete(task_id):
            status = "completed"
    return {
        "task_id": task_id,
        "status": status,
        "current_stage": progress.get("current_stage"),
        "progress_percent": progress.get("progress_percent", 0),
        "is_using_cache": is_using_cache,
        "stages": progress.get("stages", []),
    }


@router.get("/tasks/{task_id}/results")
async def get_task_results(task_id: str):
    result = tasks_results.get(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")

    status = result.get("status", "running")
    if status == "running" and not tracker.is_complete(task_id):
        progress = tracker.get_progress(task_id)
        return {
            "task_id": task_id,
            "status": "running",
            "progress_percent": progress.get("progress_percent", 0),
            "current_stage": progress.get("current_stage"),
            "message": "任务正在进行中",
        }

    deliverables = {
        "goal_analysis": result.get("goal_analysis", {}),
        "categories": result.get("categories", []),
        "findings": result.get("findings", []),
        "prd": result.get("prd", {}),
        "test_cases": result.get("test_cases", []),
        "verification": result.get("verification", {}),
        "cleaning_report": result.get("cleaning_report", {}),
        "app_info": result.get("app_info", {}),
    }

    return {
        "task_id": task_id,
        "status": status,
        "data_source": result.get("data_source", ""),
        "is_using_cache": result.get("data_source") == "cache",
        "is_fallback": result.get("is_fallback", False),
        "deliverables": deliverables,
        "error": result.get("error"),
    }


@router.post("/import", response_model=ImportResponse)
async def import_reviews(file: UploadFile = File(...), user_goal: Optional[str] = Query(default="")):
    filename = file.filename or ""
    content = await file.read()
    import_id = str(uuid.uuid4())

    try:
        if filename.lower().endswith(".json"):
            result = file_importer.import_json(content)
        elif filename.lower().endswith(".csv"):
            result = file_importer.import_csv(content)
        else:
            raise HTTPException(status_code=400, detail="仅支持 .json 或 .csv 格式文件")

        valid_reviews = result.get("valid_reviews", [])
        if valid_reviews:
            task_id = str(uuid.uuid4())
            tasks_results[task_id] = {"task_id": task_id, "status": "running"}
            tracker.init_task(task_id)

            def _run_imported(task_id: str, reviews: list, user_goal: str):
                try:
                    bundle_id = f"imported_{import_id[:8]}"
                    filters = {}
                    from app.cleaner.review_cleaner import ReviewCleaner
                    from app.analyzer.goal_understander import GoalUnderstander
                    from app.analyzer.classifier import DynamicClassifier
                    from app.analyzer.finding_generator import FindingGenerator
                    from app.analyzer.evidence_evaluator import EvidenceEvaluator
                    from app.generator.prd_generator import PRDGenerator
                    from app.generator.test_case_generator import TestCaseGenerator
                    from app.generator.traceability_checker import TraceabilityChecker

                    tracker.update(task_id, "scope_definition", "in_progress")
                    gu = GoalUnderstander(pipeline.llm_client)
                    goal_analysis = gu.understand(user_goal)
                    tracker.update(task_id, "scope_definition", "completed")

                    tracker.update(task_id, "data_collection", "in_progress")
                    tracker.update(task_id, "data_collection", "completed")

                    tracker.update(task_id, "data_cleaning", "in_progress")
                    cleaner = ReviewCleaner()
                    clean_result = cleaner.clean(reviews)
                    cleaned_reviews = clean_result.get("cleaned_reviews", [])
                    tracker.update(task_id, "data_cleaning", "completed")

                    tracker.update(task_id, "classification", "in_progress")
                    focus_areas = goal_analysis.get("focus_areas", ["全面分析"])
                    classifier = DynamicClassifier(pipeline.llm_client)
                    categories = classifier.classify(cleaned_reviews, focus_areas)
                    tracker.update(task_id, "classification", "completed")

                    tracker.update(task_id, "evidence_evaluation", "in_progress")
                    fg = FindingGenerator(pipeline.llm_client)
                    if pipeline.llm_client.is_available():
                        findings = fg.generate(categories, cleaned_reviews, user_goal)
                    else:
                        findings = fg._fallback_findings(categories, cleaned_reviews)
                    ee = EvidenceEvaluator()
                    findings = ee.evaluate(findings, cleaned_reviews)
                    tracker.update(task_id, "evidence_evaluation", "completed")

                    tracker.update(task_id, "prd_generation", "in_progress")
                    prd_gen = PRDGenerator(pipeline.llm_client)
                    prd = prd_gen.generate(findings, user_goal)
                    tracker.update(task_id, "prd_generation", "completed")

                    tracker.update(task_id, "test_case_generation", "in_progress")
                    tc_gen = TestCaseGenerator(pipeline.llm_client)
                    requirements = prd.get("requirements", [])
                    test_cases = tc_gen.generate(requirements)
                    tracker.update(task_id, "test_case_generation", "completed")

                    tracker.update(task_id, "traceability_verification", "in_progress")
                    tc_check = TraceabilityChecker(pipeline.llm_client)
                    verification = tc_check.check(cleaned_reviews, findings, requirements, test_cases)
                    tracker.update(task_id, "traceability_verification", "completed")

                    tracker.update(task_id, "result_preparation", "in_progress")
                    tasks_results[task_id] = {
                        "task_id": task_id,
                        "status": "completed",
                        "data_source": "import",
                        "goal_analysis": goal_analysis,
                        "cleaning_report": clean_result,
                        "categories": categories,
                        "findings": findings,
                        "prd": prd,
                        "test_cases": test_cases,
                        "verification": verification,
                        "cleaned_reviews": cleaned_reviews,
                        "bundle_id": bundle_id,
                        "user_goal": user_goal,
                    }
                    tracker.update(task_id, "result_preparation", "completed")
                    tracker.update(task_id, "display", "completed")
                except Exception as e:
                    tasks_results[task_id] = {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                    }

            thread = threading.Thread(
                target=_run_imported,
                args=(task_id, valid_reviews, user_goal or ""),
                daemon=True,
            )
            thread.start()

            return ImportResponse(
                import_id=import_id,
                status="success",
                statistics={
                    **result.get("statistics", {}),
                    "task_id": task_id,
                },
            )
        else:
            return ImportResponse(
                import_id=import_id,
                status="no_data",
                statistics=result.get("statistics", {}),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/tasks/{task_id}/export")
async def export_task_results(task_id: str, format: str = Query(default="json", regex="^(csv|md|json)$")):
    result = tasks_results.get(task_id)
    if not result or result.get("status") not in ("completed", "failed"):
        if not tracker.is_complete(task_id):
            raise HTTPException(status_code=400, detail="任务尚未完成，无法导出")

    if format == "json":
        export_data = {
            "task_id": task_id,
            "bundle_id": result.get("bundle_id", ""),
            "user_goal": result.get("user_goal", ""),
            "status": result.get("status", ""),
            "data_source": result.get("data_source", ""),
            "goal_analysis": result.get("goal_analysis", {}),
            "cleaning_report": result.get("cleaning_report", {}),
            "categories": result.get("categories", []),
            "findings": result.get("findings", []),
            "prd": result.get("prd", {}),
            "test_cases": result.get("test_cases", []),
            "verification": result.get("verification", {}),
        }
        content = json.dumps(export_data, ensure_ascii=False, indent=2)
        file_bytes = io.BytesIO(content.encode("utf-8"))
        media_type = "application/json"
        filename = f"task_{task_id}_result.json"
    elif format == "csv":
        from app.utils.exporter import export_reviews_csv, export_testcases_csv
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        reviews_path = os.path.join(temp_dir, f"reviews_{task_id}.csv")
        testcases_path = os.path.join(temp_dir, f"testcases_{task_id}.csv")
        export_reviews_csv(result.get("cleaned_reviews", []), reviews_path)
        export_testcases_csv(result.get("test_cases", []), testcases_path)

        import zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(reviews_path, arcname=f"reviews_{task_id}.csv")
            zf.write(testcases_path, arcname=f"testcases_{task_id}.csv")
        zip_buffer.seek(0)
        file_bytes = zip_buffer
        media_type = "application/zip"
        filename = f"task_{task_id}_export.zip"
    else:
        lines = []
        lines.append(f"# 分析报告 - 任务 {task_id}\n")
        lines.append(f"- 状态: {result.get('status', '')}")
        lines.append(f"- 数据源: {result.get('data_source', '')}")
        lines.append(f"- 用户目标: {result.get('user_goal', '')}\n")
        prd = result.get("prd", {})
        lines.append("## 版本规划\n")
        vp = prd.get("version_plan", {})
        for k, v in vp.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("\n## 需求列表\n")
        for req in prd.get("requirements", []):
            lines.append(f"### {req.get('id', '')} {req.get('title', '')}\n")
            lines.append(f"- 优先级: {req.get('priority', '')}")
            lines.append(f"- 建议版本: {req.get('version_suggestion', '')}")
            lines.append(f"- 用户故事: {req.get('user_story', '')}\n")
        lines.append("## 测试用例\n")
        for tc in result.get("test_cases", []):
            lines.append(f"### [{tc.get('type', '')}] {tc.get('title', '')}\n")
            lines.append(f"- 关联需求: {tc.get('requirement_id', '')}")
            lines.append(f"- 前置条件: {tc.get('preconditions', '')}")
            lines.append(f"- Given: {tc.get('given', '')}")
            lines.append(f"- When: {tc.get('when', '')}")
            lines.append(f"- Then: {tc.get('then', '')}\n")
        content = "\n".join(lines)
        file_bytes = io.BytesIO(content.encode("utf-8"))
        media_type = "text/markdown; charset=utf-8"
        filename = f"task_{task_id}_report.md"

    response = StreamingResponse(
        file_bytes,
        media_type=media_type,
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.get("/health", response_model=HealthResponse)
async def health_check():
    llm_ok = pipeline.llm_client.is_available()
    network_ok = False
    try:
        import requests
        resp = requests.get("https://itunes.apple.com/lookup?id=364709193", timeout=5)
        network_ok = resp.status_code == 200
    except Exception:
        network_ok = False
    return HealthResponse(
        network=network_ok,
        llm=llm_ok,
    )
