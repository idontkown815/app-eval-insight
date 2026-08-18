import json

from app.analyzer.llm_client import LLMClient


class TraceabilityChecker:
    SYSTEM = "你是质量保证专家，请检查追溯链的完整性和合理性。"

    USER_TEMPLATE = """请基于以下数据检查追溯链（Reviews → Findings → Requirements → Test Cases）的完整性和合理性。

Reviews 摘要（review_ids）：
{review_ids}

Findings：
{findings_json}

Requirements：
{requirements_json}

Test Cases：
{test_cases_json}

请输出JSON格式，包含 issues 数组，每条 issue 包含：
- type: 问题类型（missing_link/weak_evidence/inconsistency/other）
- severity: 严重程度（high/medium/low）
- description: 问题描述
- location: 问题位置（finding/requirement/test_case + ID）

只输出JSON，不要其他文字。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def check(self, reviews: list, findings: list, requirements: list, test_cases: list) -> dict:
        issues = self._rule_based_check(reviews, findings, requirements, test_cases)

        if self.llm_client.is_available():
            try:
                llm_issues = self._llm_based_check(reviews, findings, requirements, test_cases)
                issues.extend(llm_issues)
            except Exception:
                pass

        passed_items = []
        has_high = any(i.get("severity") == "high" for i in issues)
        overall_status = "fail" if has_high else "pass"

        summary_parts = []
        high_count = sum(1 for i in issues if i.get("severity") == "high")
        medium_count = sum(1 for i in issues if i.get("severity") == "medium")
        low_count = sum(1 for i in issues if i.get("severity") == "low")
        if issues:
            summary_parts.append(f"发现 {len(issues)} 个问题：高严重度 {high_count}，中 {medium_count}，低 {low_count}")
        else:
            summary_parts.append("追溯链检查通过，未发现问题")

        return {
            "passed": passed_items,
            "issues": issues,
            "overall_status": overall_status,
            "summary": "；".join(summary_parts),
        }

    def _rule_based_check(self, reviews: list, findings: list, requirements: list, test_cases: list) -> list:
        issues = []
        review_ids = {r.get("review_id") for r in reviews if r.get("review_id")}

        for f_idx, finding in enumerate(findings):
            supporting_ids = finding.get("supporting_review_ids", [])
            valid_ids = [rid for rid in supporting_ids if rid in review_ids]
            if len(valid_ids) < 3:
                fid = finding.get("id") if finding.get("id") is not None else f_idx
                issues.append({
                    "type": "weak_evidence",
                    "severity": "high",
                    "description": f"发现 {fid} 仅有 {len(valid_ids)} 条有效支撑评价，不足3条",
                    "location": f"finding:{fid}",
                })

        finding_ids = set()
        for i, f in enumerate(findings):
            fid = f.get("id") if f.get("id") is not None else i
            finding_ids.add(str(fid))
            finding_ids.add(fid)

        for r_idx, req in enumerate(requirements):
            req_fid = req.get("finding_id")
            if req_fid is not None and str(req_fid) not in finding_ids and req_fid not in finding_ids:
                rid = req.get("id") if req.get("id") is not None else r_idx
                issues.append({
                    "type": "missing_link",
                    "severity": "medium",
                    "description": f"需求 {rid} 引用的 finding_id {req_fid} 不存在",
                    "location": f"requirement:{rid}",
                })

        req_ids = set()
        for i, r in enumerate(requirements):
            rid = r.get("id") if r.get("id") is not None else i
            req_ids.add(str(rid))
            req_ids.add(rid)

        for tc_idx, tc in enumerate(test_cases):
            tc_req_id = tc.get("requirement_id")
            if tc_req_id is not None and str(tc_req_id) not in req_ids and tc_req_id not in req_ids:
                issues.append({
                    "type": "missing_link",
                    "severity": "medium",
                    "description": f"测试用例 {tc_idx} 引用的 requirement_id {tc_req_id} 不存在",
                    "location": f"test_case:{tc_idx}",
                })

        return issues

    def _llm_based_check(self, reviews: list, findings: list, requirements: list, test_cases: list) -> list:
        if not self.llm_client.is_available():
            return []

        review_ids = [r.get("review_id") for r in reviews if r.get("review_id")]
        try:
            result = self.llm_client.chat_json(
                self.SYSTEM,
                self.USER_TEMPLATE.format(
                    review_ids=json.dumps(review_ids[:50], ensure_ascii=False),
                    findings_json=json.dumps(findings, ensure_ascii=False),
                    requirements_json=json.dumps(requirements, ensure_ascii=False),
                    test_cases_json=json.dumps(test_cases, ensure_ascii=False),
                ),
            )
            return result.get("issues", [])
        except Exception:
            return []
