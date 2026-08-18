POSITIVE_WORDS = ["good", "great", "love", "excellent", "perfect", "amazing", "best"]
NEGATIVE_WORDS = ["bad", "terrible", "hate", "crash", "bug", "slow", "worst", "broken"]


class FallbackAnalyzer:
    def analyze(self, reviews: list, user_goal: str) -> dict:
        positive_ids = []
        negative_ids = []
        neutral_ids = []

        for r in reviews:
            rid = r.get("review_id", "")
            rating = r.get("rating", 0)
            content = (r.get("content", "") or "").lower()

            has_positive_word = any(w in content for w in POSITIVE_WORDS)
            has_negative_word = any(w in content for w in NEGATIVE_WORDS)

            if rating <= 2 or (has_negative_word and not has_positive_word):
                negative_ids.append(rid)
            elif rating >= 4 or (has_positive_word and not has_negative_word):
                positive_ids.append(rid)
            elif rating == 3:
                neutral_ids.append(rid)
            else:
                neutral_ids.append(rid)

        categories = []
        if positive_ids:
            categories.append({
                "name": "正面评价",
                "description": "用户表达满意或使用正面词汇的评价",
                "review_ids": positive_ids,
                "sentiment": "positive",
                "key_points": ["用户满意", "正面评价"],
            })
        if negative_ids:
            categories.append({
                "name": "负面评价",
                "description": "用户表达不满或使用负面词汇的评价",
                "review_ids": negative_ids,
                "sentiment": "negative",
                "key_points": ["用户不满", "存在问题"],
            })
        if neutral_ids:
            categories.append({
                "name": "中性评价",
                "description": "态度中立或褒贬不一的评价",
                "review_ids": neutral_ids,
                "sentiment": "neutral",
                "key_points": ["态度中立"],
            })

        findings = []
        review_map = {r.get("review_id"): r for r in reviews}
        sorted_cats = sorted(categories, key=lambda c: len(c["review_ids"]), reverse=True)
        for cat in sorted_cats[:5]:
            ids = cat["review_ids"]
            count = len(ids)
            if count > 20:
                strength = "strong"
            elif count >= 10:
                strength = "medium"
            else:
                strength = "weak"

            quotes = []
            for rid in ids[:2]:
                rv = review_map.get(rid)
                if rv:
                    c = rv.get("content", "")
                    if c:
                        quotes.append(c[:200])

            sentiment = cat["sentiment"]
            is_positive = sentiment in ("positive", "neutral")
            findings.append({
                "title": f"{cat['name']}（{count}条反馈）",
                "description": cat["description"],
                "evidence_strength": strength,
                "supporting_review_ids": ids,
                "representative_quotes": quotes,
                "suggested_action": "保持优势" if is_positive else "排查并修复问题",
                "is_positive": is_positive,
            })

        return {
            "categories": categories,
            "findings": findings,
            "is_fallback": True,
            "warning": "LLM 不可用或分析失败，已切换至降级分析模式（基于关键词和评分的简单分类，结果可能不够精准）",
        }
