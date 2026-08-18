from app.analyzer.llm_client import LLMClient


def _default_goal() -> dict:
    return {
        "focus_areas": ["全面分析"],
        "analysis_intents": ["识别问题", "评估满意度", "发现改进机会"],
        "suggested_filters": {},
    }


class GoalUnderstander:
    SYSTEM_PROMPT = "你是一个应用评审分析专家，请分析用户的分析目标。"

    USER_TEMPLATE = """请分析以下用户的应用评审分析目标，并输出结构化的JSON结果。

用户目标：{user_goal}

请输出JSON格式，包含以下字段：
- focus_areas: 字符串数组，用户关注的核心分析领域（如：功能体验、性能稳定性、UI设计、用户服务等）
- analysis_intents: 字符串数组，用户的分析意图（如：识别问题、评估满意度、发现改进机会、对比竞品等）
- suggested_filters: 对象，建议的筛选条件，可包含 rating_min、rating_max、date_start、date_end、version 等键

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def understand(self, user_goal: str) -> dict:
        if not user_goal or not user_goal.strip():
            return _default_goal()
        try:
            result = self.llm_client.chat_json(
                self.SYSTEM_PROMPT,
                self.USER_TEMPLATE.format(user_goal=user_goal),
            )
            return result
        except Exception:
            return _default_goal()
