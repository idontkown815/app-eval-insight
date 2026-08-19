"""App Store 数据采集 - 多源策略：RSS Feed + Web 爬取"""
import time

import requests

from app import config
from app.collector.web_scraper import AppStoreWebScraper


class AppStoreCrawler:
    """App Store 评论采集器。

    多源策略：
    1. 优先使用 RSS Feed API（对部分应用可用）
    2. RSS 不可用时回退到 Web 爬取（viewSoftware 页面嵌入的 JSON）
    """

    RSS_URL = (
        "https://itunes.apple.com/us/rss/customerreviews"
        "/id={bundle_id}/sortBy=mostRecent/page={page}/json"
    )

    def __init__(self):
        self.delay = config.REQUEST_DELAY_SECONDS
        self.web_scraper = AppStoreWebScraper()

    def fetch_reviews(self, bundle_id: str, max_pages: int = 10) -> list:
        """获取评论：先试 RSS，再回退到 Web 爬取。"""
        # 策略 1：RSS Feed
        try:
            rss_reviews = self._fetch_via_rss(bundle_id, max_pages)
            if rss_reviews:
                return rss_reviews
        except Exception:
            pass

        # 策略 2：Web 爬取
        try:
            web_reviews = self._fetch_via_web(bundle_id)
            if web_reviews:
                return web_reviews
        except Exception:
            pass

        raise RuntimeError(
            f"无法获取 App Store 评论 (id={bundle_id})："
            f"RSS Feed 和 Web 爬取均未返回数据。"
            f"该应用可能不支持通过公共接口获取评论。"
        )

    def _fetch_via_rss(self, bundle_id: str, max_pages: int) -> list:
        """通过 RSS Feed API 获取评论。"""
        reviews = []
        for page in range(1, max_pages + 1):
            url = self.RSS_URL.format(bundle_id=bundle_id, page=page)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                entries = data.get("feed", {}).get("entry", [])
                if not entries:
                    break
                for entry in entries:
                    parsed = self._parse_rss_entry(entry)
                    if parsed:
                        reviews.append(parsed)
            except requests.exceptions.RequestException:
                break
            except (ValueError, KeyError):
                break
            time.sleep(self.delay)
        return reviews

    def _fetch_via_web(self, bundle_id: str) -> list:
        """通过 Web 爬取获取评论。"""
        return self.web_scraper.fetch_reviews(bundle_id)

    def _parse_rss_entry(self, entry: dict) -> dict | None:
        """解析 RSS 单条评论。"""
        try:
            review_id = entry["id"]["label"]
            author = entry["author"]["name"]["label"]
            rating = int(entry["im:rating"]["label"])
            title = entry["title"]["label"]
            content = entry["content"]["label"]
            review_date = entry["updated"]["label"]
            version = entry.get("im:version", {}).get("label", "")
            return {
                "review_id": review_id,
                "author": author,
                "rating": rating,
                "title": title,
                "content": content,
                "review_date": review_date,
                "version": version,
                "source": "rss",
            }
        except (KeyError, ValueError, TypeError):
            return None
