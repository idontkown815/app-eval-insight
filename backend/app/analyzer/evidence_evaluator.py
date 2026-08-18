class EvidenceEvaluator:
    MIN_EVIDENCE = 3

    def evaluate(self, findings: list, reviews: list) -> list:
        review_map = {r.get("review_id"): r for r in reviews}

        for finding in findings:
            ids = finding.get("supporting_review_ids", [])
            count = len(ids)

            if count > 20:
                evidence_strength = "strong"
            elif count >= 10:
                evidence_strength = "medium"
            else:
                evidence_strength = "weak"
            finding["evidence_strength"] = evidence_strength

            ratings = []
            for rid in ids:
                r = review_map.get(rid)
                if r:
                    ratings.append(r.get("rating", 0))

            has_high = any(r >= 4 for r in ratings)
            has_low = any(r <= 2 for r in ratings)
            finding["is_contradictory"] = has_high and has_low

            if count < self.MIN_EVIDENCE:
                finding["data_limitation"] = "支撑评价不足"
                finding["is_hypothesis"] = True
            else:
                finding["is_hypothesis"] = False

        return findings
