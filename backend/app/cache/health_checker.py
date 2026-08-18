import requests

from app import config


class HealthChecker:
    def check_network(self) -> bool:
        try:
            response = requests.get("https://itunes.apple.com/lookup?id=839285684", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_llm(self) -> bool:
        return bool(config.LLM_API_KEY)

    def check_all(self) -> dict:
        return {
            "network": self.check_network(),
            "llm": self.check_llm(),
        }
