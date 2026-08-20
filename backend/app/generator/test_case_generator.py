import json

from app.analyzer.llm_client import LLMClient


class TestCaseGenerator:
    SYSTEM = "你是QA工程师，请基于PRD需求生成测试用例。"

    USER_TEMPLATE = """请基于以下PRD需求列表，生成对应的测试用例。

需求列表：
{requirements_json}

请输出JSON格式，包含 test_cases 数组，每条测试用例包含：
- requirement_id: 关联的需求ID
- title: 测试用例标题
- preconditions: 前置条件
- given: 给定条件
- when: 执行操作
- then: 预期结果
- type: 用例类型（positive/negative）
- source_review_ids: 来源评审ID数组（从需求的source_review_ids中选取，用于验证测试是否覆盖了用户提出的真实问题）

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(self, requirements: list) -> list:
        requirements_json = json.dumps(requirements, ensure_ascii=False, indent=2)

        if self.llm_client.is_available():
            try:
                result = self.llm_client.chat_json(
                    self.SYSTEM,
                    self.USER_TEMPLATE.format(requirements_json=requirements_json),
                )
                test_cases = result.get("test_cases", [])
                # 确保 source_review_ids 被填充（LLM 可能遗漏）
                req_map = {r.get("id"): r for r in requirements}
                for tc in test_cases:
                    tc["generated_by"] = "llm"
                    if not tc.get("source_review_ids"):
                        req = req_map.get(tc.get("requirement_id"), {})
                        tc["source_review_ids"] = req.get("source_review_ids", [])[:3]
                return test_cases
            except Exception:
                return self._fallback_generate(requirements)
        else:
            return self._fallback_generate(requirements)

    def _fallback_generate(self, requirements: list) -> list:
        test_cases = []
        for req in requirements:
            req_id = req.get("id", "")
            req_title = req.get("title", "")
            source_rids = req.get("source_review_ids", [])

            test_cases.append({
                "requirement_id": req_id,
                "title": f"{req_title} - 正向验证",
                "preconditions": "系统正常运行，用户已登录",
                "given": "用户已完成前置条件",
                "when": "执行需求相关操作",
                "then": "功能按预期正常工作，用户反馈的问题不再出现",
                "type": "positive",
                "source_review_ids": source_rids[:2],
                "generated_by": "rule_based",
            })

            test_cases.append({
                "requirement_id": req_id,
                "title": f"{req_title} - 异常处理",
                "preconditions": "系统处于异常或边界条件下",
                "given": "用户处于异常环境",
                "when": "执行需求相关操作",
                "then": "系统友好提示错误，不崩溃",
                "type": "negative",
                "source_review_ids": source_rids[:2],
                "generated_by": "rule_based",
            })

        return test_cases
