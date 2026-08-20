import re
from collections import Counter

from dateutil import parser as date_parser


class ReviewCleaner:
    # 简单语言检测：基于 Unicode 范围和常见字符
    CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
    LATIN_PATTERN = re.compile(r'[a-zA-Z]')
    CYRILLIC_PATTERN = re.compile(r'[\u0400-\u04ff]')
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06ff]')

    def clean(self, raw_reviews: list) -> dict:
        seen_ids = set()
        seen_content_hashes = set()
        deduped = []
        duplicate_content_count = 0

        for r in raw_reviews:
            rid = r.get("review_id")
            # ID 去重
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)

            # 内容指纹去重（去除空格/标点后比较）
            content_raw = r.get("content", "")
            content_hash = self._content_fingerprint(content_raw)
            if content_hash and content_hash in seen_content_hashes:
                duplicate_content_count += 1
                continue
            if content_hash:
                seen_content_hashes.add(content_hash)

            deduped.append(r)

        cleaned = []
        languages = []
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
            lang = self._detect_language(content)

            cleaned_review = dict(r)
            cleaned_review["content"] = content
            cleaned_review["rating"] = rating
            cleaned_review["review_date"] = date
            cleaned_review["language"] = lang
            cleaned.append(cleaned_review)
            languages.append(lang)

        original_count = len(raw_reviews)
        cleaned_count = len(cleaned)
        removed_count = original_count - cleaned_count

        # 语言分布统计
        lang_dist = dict(Counter(languages))
        has_mixed_languages = len(lang_dist) > 1

        return {
            "cleaned_reviews": cleaned,
            "original_count": original_count,
            "cleaned_count": cleaned_count,
            "removed_count": removed_count,
            "duplicate_content_removed": duplicate_content_count,
            "language_distribution": lang_dist,
            "has_mixed_languages": has_mixed_languages,
        }

    @staticmethod
    def _content_fingerprint(text: str) -> str:
        """生成内容指纹：去除空格和标点后取哈希，用于检测内容重复。"""
        if not isinstance(text, str) or len(text) < 10:
            return ""
        normalized = re.sub(r'[\s\W]+', '', text.lower())
        return normalized[:200]  # 截断避免过长

    @staticmethod
    def _detect_language(text: str) -> str:
        """简单语言检测：基于字符集判断主要语言。"""
        if not text:
            return "unknown"
        cjk_count = len(ReviewCleaner.CJK_PATTERN.findall(text))
        latin_count = len(ReviewCleaner.LATIN_PATTERN.findall(text))
        cyrillic_count = len(ReviewCleaner.CYRILLIC_PATTERN.findall(text))
        arabic_count = len(ReviewCleaner.ARABIC_PATTERN.findall(text))

        if cyrillic_count > 0 and cyrillic_count >= latin_count:
            return "ru"
        if arabic_count > 0 and arabic_count >= latin_count:
            return "ar"
        if cjk_count > 0:
            # 进一步区分中日韩
            if re.search(r'[\uac00-\ud7af]', text):
                return "ko"
            if re.search(r'[\u3040-\u30ff]', text):
                return "ja"
            return "zh"
        if latin_count > 0:
            return "en"
        return "unknown"

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
