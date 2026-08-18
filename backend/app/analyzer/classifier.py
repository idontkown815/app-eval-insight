from collections import defaultdict

from app.analyzer.llm_client import LLMClient


class DynamicClassifier:
    BATCH_SIZE = 30

    SYSTEM = "你是一个应用评审分析专家，请对评价进行动态分类。"

    USER_TEMPLATE = """请根据以下关注点，对这批评价进行动态分类。

关注点：{focus_areas}

评价批次（共 {batch_size} 条）：
{reviews_text}

要求：
1. 动态生成类别，类别名要具体、有意义，反映评价的核心主题
2. 每个类别包含：名称、描述、关联的review_id数组、情感倾向(positive/negative/neutral/mixed)、关键点数组
3. 只输出JSON格式：{{"categories": [{{"name": "...", "description": "...", "review_ids": [...], "sentiment": "...", "key_points": [...]}}]}}

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def classify(self, reviews: list, focus_areas: list) -> list:
        if not self.llm_client.is_available():
            return self._fallback_classify(reviews, focus_areas)

        all_categories = []
        for i in range(0, len(reviews), self.BATCH_SIZE):
            batch = reviews[i:i + self.BATCH_SIZE]
            reviews_text = self._format_reviews(batch)
            try:
                result = self.llm_client.chat_json(
                    self.SYSTEM,
                    self.USER_TEMPLATE.format(
                        focus_areas=focus_areas,
                        batch_size=len(batch),
                        reviews_text=reviews_text,
                    ),
                )
                batch_categories = result.get("categories", [])
                all_categories.extend(batch_categories)
            except Exception:
                fallback_cats = self._fallback_classify(batch, focus_areas)
                all_categories.extend(fallback_cats)

        return self._merge_similar(all_categories)

    def _format_reviews(self, reviews: list) -> str:
        lines = []
        for r in reviews:
            rid = r.get("review_id", "")
            rating = r.get("rating", "")
            content = r.get("content", "")
            lines.append(f"[ID:{rid}] 评分:{rating} 内容:{content}")
        return "\n".join(lines)

    @staticmethod
    def _merge_similar(categories: list) -> list:
        grouped = defaultdict(lambda: {
            "name": "",
            "description": "",
            "review_ids": [],
            "sentiment": "mixed",
            "key_points": [],
        })
        for cat in categories:
            name = cat.get("name", "未分类")
            entry = grouped[name]
            entry["name"] = name
            if not entry["description"]:
                entry["description"] = cat.get("description", "")
            entry["review_ids"].extend(cat.get("review_ids", []))
            sentiments = [entry["sentiment"]] + [cat.get("sentiment", "neutral")]
            unique_sentiments = set(sentiments)
            if len(unique_sentiments) > 1:
                entry["sentiment"] = "mixed"
            else:
                entry["sentiment"] = list(unique_sentiments)[0]
            for kp in cat.get("key_points", []):
                if kp not in entry["key_points"]:
                    entry["key_points"].append(kp)
        return list(grouped.values())

    def _fallback_classify(self, reviews: list, focus_areas: list) -> list:
        negative_ids = []
        neutral_ids = []
        positive_ids = []

        for r in reviews:
            rating = r.get("rating", 0)
            rid = r.get("review_id", "")
            if rating <= 2:
                negative_ids.append(rid)
            elif rating == 3:
                neutral_ids.append(rid)
            else:
                positive_ids.append(rid)

        categories = []
        if negative_ids:
            categories.append({
                "name": "负面反馈",
                "description": "评分1-2星的差评，主要反映用户不满的问题",
                "review_ids": negative_ids,
                "sentiment": "negative",
                "key_points": ["用户不满", "需要改进"],
            })
        if neutral_ids:
            categories.append({
                "name": "中性反馈",
                "description": "评分3星的中评，用户态度中立或褒贬不一",
                "review_ids": neutral_ids,
                "sentiment": "neutral",
                "key_points": ["态度中立", "有褒有贬"],
            })
        if positive_ids:
            categories.append({
                "name": "正面反馈",
                "description": "评分4-5星的好评，主要反映用户满意的方面",
                "review_ids": positive_ids,
                "sentiment": "positive",
                "key_points": ["用户满意", "表现优秀"],
            })
        return categories
