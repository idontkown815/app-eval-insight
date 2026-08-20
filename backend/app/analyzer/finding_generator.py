import json

from app.analyzer.llm_client import LLMClient


class FindingGenerator:
    SYSTEM = "你是一个应用评审分析专家，请基于分类结果生成关键发现。"

    USER_TEMPLATE = """请基于以下分类结果，生成最多5条关键发现。

用户分析目标：{user_goal}

分类结果摘要：
{cat_summary}

要求：
1. 每条发现包含：title(标题)、description(详细描述)、evidence_strength(strong/medium/weak)、supporting_review_ids(支撑review_id数组)、representative_quotes(代表性引用数组)、suggested_action(建议行动)、is_positive(布尔值，是否为正面发现)
2. 优先选择最有价值、数据支撑最充分的发现
3. 正面和负面发现都应涵盖

只输出JSON格式：{{"findings": [{{...}}]}}

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(self, categories: list, reviews: list, user_goal: str) -> list:
        if not self.llm_client.is_available():
            return self._fallback_findings(categories, reviews)

        cat_summary_list = []
        for cat in categories:
            cat_summary_list.append({
                "name": cat.get("name", ""),
                "count": len(cat.get("review_ids", [])),
                "sentiment": cat.get("sentiment", "neutral"),
                "description": cat.get("description", ""),
                "key_points": cat.get("key_points", []),
            })
        cat_summary = json.dumps(cat_summary_list, ensure_ascii=False, indent=2)

        try:
            result = self.llm_client.chat_json(
                self.SYSTEM,
                self.USER_TEMPLATE.format(
                    user_goal=user_goal,
                    cat_summary=cat_summary,
                ),
            )
            findings = result.get("findings", [])
            for f in findings:
                f["generated_by"] = "llm"
            return findings
        except Exception:
            findings = self._fallback_findings(categories, reviews)
            for f in findings:
                f["generated_by"] = "rule_based"
            return findings

    def _fallback_findings(self, categories: list, reviews: list) -> list:
        review_map = {r.get("review_id"): r for r in reviews}
        findings = []

        sorted_categories = sorted(
            categories,
            key=lambda c: len(c.get("review_ids", [])),
            reverse=True,
        )

        for cat in sorted_categories[:5]:
            review_ids = cat.get("review_ids", [])
            count = len(review_ids)

            if count > 20:
                evidence_strength = "strong"
            elif count >= 10:
                evidence_strength = "medium"
            else:
                evidence_strength = "weak"

            representative_quotes = []
            for rid in review_ids[:2]:
                r = review_map.get(rid)
                if r:
                    content = r.get("content", "")
                    if content:
                        representative_quotes.append(content[:200])

            sentiment = cat.get("sentiment", "neutral")
            is_positive = sentiment in ("positive", "neutral")

            finding = {
                "title": f"{cat.get('name', '未分类')}（{count}条反馈）",
                "description": cat.get("description", ""),
                "evidence_strength": evidence_strength,
                "supporting_review_ids": review_ids,
                "representative_quotes": representative_quotes,
                "suggested_action": "持续关注该类反馈，根据具体情况优化改进" if not is_positive else "保持并持续优化",
                "is_positive": is_positive,
            }
            findings.append(finding)

        return findings
