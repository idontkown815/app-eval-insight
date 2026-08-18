import json
import csv
import io


class FileImporter:
    REQUIRED_FIELDS = ["review_id", "rating", "content", "review_date"]

    def import_json(self, file_bytes: bytes) -> dict:
        data = json.loads(file_bytes.decode("utf-8"))
        reviews = data.get("reviews", [])
        return self._validate_reviews(reviews)

    def import_csv(self, file_bytes: bytes) -> dict:
        content = file_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        reviews = list(reader)
        return self._validate_reviews(reviews)

    def _validate_reviews(self, reviews: list) -> dict:
        valid = []
        invalid_count = 0
        for r in reviews:
            try:
                for field in self.REQUIRED_FIELDS:
                    if field not in r or r[field] is None or r[field] == "":
                        raise KeyError(field)
                r["rating"] = int(r["rating"])
                valid.append(r)
            except (KeyError, ValueError, TypeError):
                invalid_count += 1
        return {
            "valid_reviews": valid,
            "invalid_count": invalid_count,
            "total_count": len(reviews),
            "statistics": {
                "valid": len(valid),
                "invalid": invalid_count,
            },
        }
