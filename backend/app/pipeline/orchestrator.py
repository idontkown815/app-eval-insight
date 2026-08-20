from app.analyzer.llm_client import LLMClient
from app.analyzer.goal_understander import GoalUnderstander
from app.analyzer.classifier import DynamicClassifier
from app.analyzer.finding_generator import FindingGenerator
from app.analyzer.evidence_evaluator import EvidenceEvaluator
from app.generator.prd_generator import PRDGenerator
from app.generator.test_case_generator import TestCaseGenerator
from app.generator.traceability_checker import TraceabilityChecker
from app.cache.cache_manager import CacheManager
from app.collector.app_store import AppStoreCrawler
from app.cleaner.review_cleaner import ReviewCleaner
from app.pipeline.stage_tracker import StageTracker


class PipelineOrchestrator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.goal_understander = GoalUnderstander(self.llm_client)
        self.classifier = DynamicClassifier(self.llm_client)
        self.finding_generator = FindingGenerator(self.llm_client)
        self.evidence_evaluator = EvidenceEvaluator()
        self.prd_generator = PRDGenerator(self.llm_client)
        self.test_case_generator = TestCaseGenerator(self.llm_client)
        self.traceability_checker = TraceabilityChecker(self.llm_client)
        self.cache_manager = CacheManager()
        self.crawler = AppStoreCrawler()
        self.cleaner = ReviewCleaner()
        self.tracker = StageTracker()

    def run(self, task_id: str, bundle_id: str, user_goal: str, filters: dict = None, app_info: dict = None) -> dict:
        filters = filters or {}
        results = {}
        cleaned_reviews = []

        try:
            self.tracker.update(task_id, "scope_definition", "in_progress")
            goal_analysis = self.goal_understander.understand(user_goal)
            results["goal_analysis"] = goal_analysis
            self.tracker.update(task_id, "scope_definition", "completed")
        except Exception as e:
            self.tracker.update(task_id, "scope_definition", "failed")
            results["error"] = f"阶段1-scope_definition失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "data_collection", "in_progress")
            raw_reviews = None
            data_source = "live"
            try:
                raw_reviews = self.crawler.fetch_reviews(bundle_id)
                if raw_reviews:
                    self.cache_manager.save_reviews(bundle_id, raw_reviews)
            except Exception as fetch_err:
                # 实时抓取失败，尝试缓存
                cached = self.cache_manager.get_cached_reviews(bundle_id)
                if cached:
                    raw_reviews = cached.get("reviews", [])
                    data_source = "cache"
                else:
                    # 提供清晰的错误信息，区分不同原因
                    error_msg = str(fetch_err)
                    if "RSS Feed 和 Web 爬取均未返回数据" in error_msg:
                        raise RuntimeError(
                            f"无法获取该应用的评价数据 (id={bundle_id})。"
                            f"原因：Apple 官方 RSS Feed API 对该应用不可用，"
                            f"且网页爬取也未找到评价。"
                            f"这可能是因为：\n"
                            f"1. 该应用在 App Store 上没有公开评价\n"
                            f"2. Apple 对该应用的评价接口做了限制\n"
                            f"3. 网络连接问题（请检查网络后重试）\n\n"
                            f"建议：尝试使用 CSV/JSON 文件导入功能，"
                            f"或选择其他有评价的应用。"
                        )
                    elif "连接被 Apple 拒绝" in error_msg or "ConnectionResetError" in error_msg:
                        raise RuntimeError(
                            f"请求被 App Store 拒绝 (id={bundle_id})。"
                            f"这可能是因为请求过于频繁被限流。"
                            f"请等待几分钟后重试，或使用文件导入功能。"
                        )
                    else:
                        raise RuntimeError(
                            f"获取评价数据失败 (id={bundle_id})：{error_msg}"
                        )
            if not raw_reviews:
                cached = self.cache_manager.get_cached_reviews(bundle_id)
                if cached:
                    raw_reviews = cached.get("reviews", [])
                    data_source = "cache"
                else:
                    raise RuntimeError(
                        f"未获取到任何评价数据 (id={bundle_id})。"
                        f"App Store 可能未公开该应用的评价。"
                        f"请尝试其他应用，或使用文件导入功能。"
                    )
            results["raw_reviews"] = raw_reviews
            results["data_source"] = data_source
            results["data_fetch_note"] = self._build_data_note(raw_reviews, data_source)
            self.tracker.update(task_id, "data_collection", "completed")
        except Exception as e:
            self.tracker.update(task_id, "data_collection", "failed")
            results["error"] = f"阶段2-数据收集失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "data_cleaning", "in_progress")
            clean_result = self.cleaner.clean(results["raw_reviews"])
            cleaned_reviews = clean_result.get("cleaned_reviews", [])
            clean_report = {
                "original_count": clean_result.get("original_count", 0),
                "cleaned_count": clean_result.get("cleaned_count", 0),
                "removed_count": clean_result.get("removed_count", 0),
                "duplicate_content_removed": clean_result.get("duplicate_content_removed", 0),
                "language_distribution": clean_result.get("language_distribution", {}),
                "has_mixed_languages": clean_result.get("has_mixed_languages", False),
            }
            results["cleaning_report"] = clean_report
            self.tracker.update(task_id, "data_cleaning", "completed")
        except Exception as e:
            self.tracker.update(task_id, "data_cleaning", "failed")
            results["error"] = f"阶段3-data_cleaning失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "classification", "in_progress")
            focus_areas = goal_analysis.get("focus_areas", ["全面分析"])
            categories = self.classifier.classify(cleaned_reviews, focus_areas)
            if not self.llm_client.is_available():
                results["is_fallback"] = True
            else:
                results["is_fallback"] = False
            results["categories"] = categories
            self.tracker.update(task_id, "classification", "completed")
        except Exception as e:
            self.tracker.update(task_id, "classification", "failed")
            results["error"] = f"阶段4-classification失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "evidence_evaluation", "in_progress")
            if self.llm_client.is_available():
                findings = self.finding_generator.generate(categories, cleaned_reviews, user_goal)
            else:
                findings = self.finding_generator._fallback_findings(categories, cleaned_reviews)
            findings = self.evidence_evaluator.evaluate(findings, cleaned_reviews)
            results["findings"] = findings
            self.tracker.update(task_id, "evidence_evaluation", "completed")
        except Exception as e:
            self.tracker.update(task_id, "evidence_evaluation", "failed")
            results["error"] = f"阶段5-evidence_evaluation失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "prd_generation", "in_progress")
            prd = self.prd_generator.generate(findings, user_goal)
            results["prd"] = prd
            self.tracker.update(task_id, "prd_generation", "completed")
        except Exception as e:
            self.tracker.update(task_id, "prd_generation", "failed")
            results["error"] = f"阶段6-prd_generation失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "test_case_generation", "in_progress")
            requirements = prd.get("requirements", [])
            test_cases = self.test_case_generator.generate(requirements)
            results["test_cases"] = test_cases
            self.tracker.update(task_id, "test_case_generation", "completed")
        except Exception as e:
            self.tracker.update(task_id, "test_case_generation", "failed")
            results["error"] = f"阶段7-test_case_generation失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "traceability_verification", "in_progress")
            verification = self.traceability_checker.check(
                cleaned_reviews,
                findings,
                requirements,
                test_cases,
            )
            results["verification"] = verification
            self.tracker.update(task_id, "traceability_verification", "completed")
        except Exception as e:
            self.tracker.update(task_id, "traceability_verification", "failed")
            results["error"] = f"阶段8-traceability_verification失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "result_preparation", "in_progress")
            results["cleaned_reviews"] = cleaned_reviews
            results["task_id"] = task_id
            results["bundle_id"] = bundle_id
            results["user_goal"] = user_goal
            results["app_info"] = app_info or {}
            results["status"] = "completed"
            self.tracker.update(task_id, "result_preparation", "completed")
        except Exception as e:
            self.tracker.update(task_id, "result_preparation", "failed")
            results["error"] = f"阶段9-result_preparation失败: {str(e)}"
            results["task_id"] = task_id
            results["status"] = "failed"
            return results

        try:
            self.tracker.update(task_id, "display", "completed")
        except Exception:
            pass

        return results

    @staticmethod
    def _build_data_note(raw_reviews: list, data_source: str) -> str:
        """构建数据来源和局限性的透明说明。"""
        count = len(raw_reviews)
        if not raw_reviews:
            return "未获取到评价数据"

        # 检查来源标记
        sources = set()
        for r in raw_reviews:
            src = r.get("source", "")
            if src:
                sources.add(src)

        if data_source == "cache":
            return (
                f"数据来源：本地缓存（{count} 条评价）。"
                f"实时采集失败，使用上次缓存的数据。"
                f"缓存可能已过期，建议稍后重试实时采集。"
            )

        if "rss" in sources and "web" not in sources:
            return (
                f"数据来源：Apple RSS Feed API（{count} 条评价）。"
                f"这是 Apple 官方公开的评价数据接口，数据真实可重复。"
            )

        if "web" in sources or "rss" not in sources:
            return (
                f"数据来源：App Store 网页数据（{count} 条评价）。"
                f"Apple RSS Feed API 对该应用未返回数据，"
                f"通过解析 App Store 页面嵌入的 JSON 获取。"
                f"局限性：页面通常只包含精选评价（最多约40条），"
                f"不代表全部用户评价。如需更多数据，请使用文件导入功能。"
            )

        return f"数据来源：App Store（{count} 条评价）"
