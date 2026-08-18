import re
import requests

from app import config


class LinkParser:
    URL_PATTERN = r'https://apps\.apple\.com/us/app/[^/]+/id(\d+)'
    LOOKUP_URL = "https://itunes.apple.com/lookup?id={bundle_id}"

    def parse(self, url: str) -> dict:
        match = re.search(self.URL_PATTERN, url)
        if not match:
            raise ValueError("无效的 App Store US 链接")
        return {"valid": True, "bundle_id": match.group(1)}

    def fetch_app_info(self, bundle_id: str) -> dict:
        url = self.LOOKUP_URL.format(bundle_id=bundle_id)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("resultCount", 0) == 0:
                raise ValueError("未找到该应用信息")
            result = data["results"][0]
            return {
                "name": result.get("trackName", ""),
                "developer": result.get("artistName", ""),
                "price": result.get("price", 0),
                "category": result.get("primaryGenreName", ""),
                "icon_url": result.get("artworkUrl100", ""),
                "rating": result.get("averageUserRating", 0),
                "review_count": result.get("userRatingCount", 0),
            }
        except requests.exceptions.RequestException as e:
            raise ValueError(f"获取应用信息失败: {str(e)}")
        except (ValueError, KeyError) as e:
            raise ValueError(f"解析应用信息失败: {str(e)}")
