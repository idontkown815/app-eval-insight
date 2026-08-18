import os
import json
from datetime import datetime, timedelta

from app import config


class CacheManager:
    def __init__(self):
        self.cache_dir = config.CACHE_DIR or "./data/cache"
        self.validity_days = int(config.CACHE_VALIDITY_DAYS or 7)

    def save_reviews(self, bundle_id: str, reviews: list) -> dict:
        now = datetime.now()
        timestamp = now.strftime("%Y%m%dT%H%M%S")
        cache_id = f"{bundle_id}_{timestamp}"
        filepath = os.path.join(self.cache_dir, "reviews", f"{cache_id}.json")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        meta = {
            "cache_id": cache_id,
            "bundle_id": bundle_id,
            "collected_at": now.isoformat(),
            "review_count": len(reviews),
            "validity_days": self.validity_days,
            "status": "active",
            "filepath": filepath,
        }
        self._update_index(meta)
        return meta

    def get_cached_reviews(self, bundle_id: str) -> dict | None:
        index = self._read_index()
        matches = [m for m in index if m.get("bundle_id") == bundle_id]
        if not matches:
            return None
        matches_sorted = sorted(matches, key=lambda x: x.get("collected_at", ""), reverse=True)
        latest = matches_sorted[0]
        try:
            collected_at = datetime.fromisoformat(latest["collected_at"])
        except (ValueError, KeyError):
            return None
        if datetime.now() > collected_at + timedelta(days=self.validity_days):
            latest["status"] = "expired"
        try:
            with open(latest["filepath"], "r", encoding="utf-8") as f:
                reviews = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
        return {"meta": latest, "reviews": reviews}

    def _read_index(self) -> list:
        index_path = os.path.join(self.cache_dir, "cache_index.json")
        if not os.path.exists(index_path):
            return []
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _update_index(self, meta: dict):
        index = self._read_index()
        index.append(meta)
        index_path = os.path.join(self.cache_dir, "cache_index.json")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
