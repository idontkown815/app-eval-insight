"""App Store Web 评论爬取 - 从 viewSoftware 页面解析嵌入的 JSON 数据"""
import json
import re
import time

import requests

from app import config


class AppStoreWebScraper:
    """从 App Store viewSoftware 页面爬取评论。

    Apple 的 viewSoftware 页面 (https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware)
    在 HTML 中嵌入了包含评论数据的 JSON。本类解析该 JSON 以提取评论。

    注意：该页面通常只包含最多 40 条精选评论（多为 5 星），
    需配合 RSS Feed 或 iTunes Lookup API 评分数据使用。
    """

    VIEW_SOFTWARE_URL = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self):
        self.delay = config.REQUEST_DELAY_SECONDS

    def fetch_reviews(self, bundle_id: str, max_retries: int = 2) -> list:
        """从 App Store 页面获取评论，返回标准化的评论列表。"""
        url = f"{self.VIEW_SOFTWARE_URL}?id={bundle_id}&cc=us"

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, headers=self.DEFAULT_HEADERS, timeout=20
                )
                response.raise_for_status()
                reviews = self._parse_reviews_from_html(response.text)
                if reviews:
                    return reviews
                # 如果没有评论，可能是页面结构变化或应用无评论
                return []
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(self.delay * 2)
                    continue
                raise RuntimeError(
                    f"App Store Web 请求失败 (id={bundle_id})："
                    f"连接被 Apple 拒绝或网络超时"
                )
            except (json.JSONDecodeError, ValueError) as e:
                raise RuntimeError(
                    f"App Store Web 数据解析失败 (id={bundle_id})：{str(e)}"
                )

        return []

    def _parse_reviews_from_html(self, html: str) -> list:
        """从 HTML 中提取嵌入的 JSON 数据并解析评论。"""
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
        if not scripts:
            return []

        # 找最大的 script（包含 JSON 数据）
        biggest = max(scripts, key=len)
        if len(biggest) < 1000:
            return []

        data = json.loads(biggest)

        # 递归搜索 $kind: "Review"
        raw_reviews = []
        self._find_reviews(data, raw_reviews)

        # 标准化并去重
        seen_ids = set()
        reviews = []
        for rev in raw_reviews:
            review_id = str(rev.get("id", ""))
            if not review_id or review_id in seen_ids:
                continue
            seen_ids.add(review_id)

            # 跳过没有内容的评论
            contents = rev.get("contents", "")
            if not contents or not isinstance(contents, str) or len(contents.strip()) < 5:
                continue

            reviews.append({
                "review_id": review_id,
                "author": rev.get("reviewerName", "Unknown"),
                "rating": int(rev.get("rating", 0)),
                "title": rev.get("title", ""),
                "content": contents,
                "review_date": rev.get("date", ""),
                "version": "",
                "source": "web",
            })

        return reviews

    @staticmethod
    def _find_reviews(obj, results: list):
        """递归查找 $kind: "Review" 的对象。"""
        if isinstance(obj, dict):
            if obj.get("$kind") == "Review":
                results.append(obj)
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    AppStoreWebScraper._find_reviews(v, results)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    AppStoreWebScraper._find_reviews(item, results)
