import re

from dateutil import parser as date_parser


class ReviewCleaner:
    def clean(self, raw_reviews: list) -> dict:
        seen_ids = set()
        deduped = []
        for r in raw_reviews:
            rid = r.get("review_id")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                deduped.append(r)

        cleaned = []
        for r in deduped:
            content = self._strip_html(r.get("content", ""))
            if content == "":
                continue
            try:
                rating = int(r["rating"])
            except (ValueError, TypeError, KeyError):
                continue
            if rating < 1 or rating > 5:
                continue
            date_str = r.get("review_date", "")
            date = self._normalize_date(date_str)
            cleaned_review = dict(r)
            cleaned_review["content"] = content
            cleaned_review["rating"] = rating
            cleaned_review["review_date"] = date
            cleaned.append(cleaned_review)

        original_count = len(raw_reviews)
        cleaned_count = len(cleaned)
        removed_count = original_count - cleaned_count
        return {
            "cleaned_reviews": cleaned,
            "original_count": original_count,
            "cleaned_count": cleaned_count,
            "removed_count": removed_count,
        }

    def _strip_html(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        return re.sub(r'<[^>]+>', '', text).strip()

    def _normalize_date(self, date_str: str) -> str:
        try:
            parsed = date_parser.parse(date_str)
            return parsed.isoformat()
        except (ValueError, TypeError, OverflowError):
            return date_str
