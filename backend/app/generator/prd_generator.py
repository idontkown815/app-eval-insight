import json

from app.analyzer.llm_client import LLMClient


class PRDGenerator:
    SYSTEM = "你是产品经理，请基于分析发现生成结构化的PRD文档。"

    USER_TEMPLATE = """请基于以下分析发现（findings），生成结构化的产品需求文档（PRD）。

分析发现列表（findings）：
{findings_summary}

用户目标：{user_goal}

请输出JSON格式，包含以下字段：
- requirements: 需求数组，每条需求包含：
  - id: 需求ID（格式如 REQ-001）
  - finding_id: 关联的发现ID或索引
  - title: 需求标题
  - user_story: 用户故事（格式：作为...我想要...以便...）
  - priority: 优先级（P0/P1/P2）
  - version_suggestion: 建议版本（V1/V2）
- version_plan: 版本规划对象，包含：
  - V1: V1版本核心内容描述
  - V2: V2版本增强内容描述

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(self, findings: list, user_goal: str) -> dict:
        findings_summary = json.dumps([
            {
                "id": idx if not f.get("id") else f.get("id"),
                "title": f.get("title", ""),
                "description": f.get("description", ""),
                "strength": f.get("evidence_strength", "medium"),
            }
            for idx, f in enumerate(findings)
        ], ensure_ascii=False)

        if self.llm_client.is_available():
            try:
                result = self.llm_client.chat_json(
                    self.SYSTEM,
                    self.USER_TEMPLATE.format(
                        findings_summary=findings_summary,
                        user_goal=user_goal or "未指定",
                    ),
                )
                return {
                    "requirements": result.get("requirements", []),
                    "version_plan": result.get("version_plan", {}),
                }
            except Exception:
                return self._fallback_generate(findings)
        else:
            return self._fallback_generate(findings)

    def _fallback_generate(self, findings: list) -> dict:
        requirements = []
        for i, f in enumerate(findings):
            strength = f.get("evidence_strength", "medium")
            if strength == "strong":
                priority = "P0"
                version_suggestion = "V1"
            elif strength == "medium":
                priority = "P1"
                version_suggestion = "V2"
            else:
                priority = "P2"
                version_suggestion = "V2"

            title = f.get("title", f"发现{i+1}")
            finding_id = f.get("id") if f.get("id") is not None else i

            requirements.append({
                "id": f"REQ-{i+1:03d}",
                "finding_id": finding_id,
                "title": title,
                "user_story": f"作为用户，我希望{title}得到解决，以便提升使用体验",
                "priority": priority,
                "version_suggestion": version_suggestion,
            })

        version_plan = {
            "V1": "核心体验与稳定性优化",
            "V2": "增强功能与用户体验完善",
        }

        return {
            "requirements": requirements,
            "version_plan": version_plan,
        }
