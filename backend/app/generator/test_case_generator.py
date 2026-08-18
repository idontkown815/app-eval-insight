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
                return result.get("test_cases", [])
            except Exception:
                return self._fallback_generate(requirements)
        else:
            return self._fallback_generate(requirements)

    def _fallback_generate(self, requirements: list) -> list:
        test_cases = []
        for req in requirements:
            req_id = req.get("id", "")
            req_title = req.get("title", "")

            test_cases.append({
                "requirement_id": req_id,
                "title": f"{req_title} - 正向验证",
                "preconditions": "系统正常运行，用户已登录",
                "given": "用户已完成前置条件",
                "when": "执行需求相关操作",
                "then": "功能按预期正常工作",
                "type": "positive",
            })

            test_cases.append({
                "requirement_id": req_id,
                "title": f"{req_title} - 异常处理",
                "preconditions": "系统处于异常或边界条件下",
                "given": "用户处于异常环境",
                "when": "执行需求相关操作",
                "then": "系统友好提示错误，不崩溃",
                "type": "negative",
            })

        return test_cases
