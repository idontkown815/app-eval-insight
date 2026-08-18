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
            except Exception:
                cached = self.cache_manager.get_cached_reviews(bundle_id)
                if cached:
                    raw_reviews = cached.get("reviews", [])
                    data_source = "cache"
                else:
                    raise RuntimeError("无法获取评价数据：实时抓取失败且无缓存")
            if not raw_reviews:
                cached = self.cache_manager.get_cached_reviews(bundle_id)
                if cached:
                    raw_reviews = cached.get("reviews", [])
                    data_source = "cache"
                else:
                    raise RuntimeError("未获取到任何评价数据")
            results["raw_reviews"] = raw_reviews
            results["data_source"] = data_source
            self.tracker.update(task_id, "data_collection", "completed")
        except Exception as e:
            self.tracker.update(task_id, "data_collection", "failed")
            results["error"] = f"阶段2-data_collection失败: {str(e)}"
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
