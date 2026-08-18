import time
import requests

from app import config


class AppStoreCrawler:
    RSS_URL = "https://itunes.apple.com/us/rss/customerreviews/id={bundle_id}/sortBy=mostRecent/page={page}/json"

    def __init__(self):
        self.delay = config.REQUEST_DELAY_SECONDS

    def fetch_reviews(self, bundle_id: str, max_pages: int = 10) -> list:
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
                    parsed = self._parse_entry(entry)
                    if parsed:
                        reviews.append(parsed)
            except requests.exceptions.RequestException:
                break
            except (ValueError, KeyError):
                break
            time.sleep(self.delay)
        return reviews

    def _parse_entry(self, entry: dict) -> dict | None:
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
            }
        except KeyError:
            return None
