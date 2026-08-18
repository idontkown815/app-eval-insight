import os
import csv
import io


def _ensure_dir(filepath: str):
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)


def export_reviews_csv(reviews: list, filepath: str = None) -> str:
    """导出评论为 CSV 字符串；若指定 filepath 同时写入文件"""
    buf = io.StringIO()
    fieldnames = ["review_id", "author", "rating", "title", "content", "review_date", "version"]
    if reviews:
        keys = list(reviews[0].keys())
        for k in keys:
            if k not in fieldnames:
                fieldnames.append(k)
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in reviews:
        row = {k: r.get(k, "") for k in fieldnames}
        writer.writerow(row)
    text = buf.getvalue()
    if filepath:
        _ensure_dir(filepath)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
    return text


def export_markdown(reviews: list, categories: list, findings: list, app_name: str,
                    prd_requirements: list, test_cases: list, filepath: str = None) -> str:
    """根据分析结果生成 Markdown 报告；若指定 filepath 同时写入文件"""
    lines = []
    lines.append(f"# 应用评价分析报告：{app_name or '未知应用'}")
    lines.append("")
    lines.append(f"- 评价总数：**{len(reviews)}** 条")
    lines.append(f"- 分类数量：**{len(categories)}** 个")
    lines.append(f"- 关键发现：**{len(findings)}** 条")
    lines.append(f"- PRD 需求：**{len(prd_requirements)}** 条")
    lines.append(f"- 测试用例：**{len(test_cases)}** 条")
    lines.append("")
    lines.append("## 关键发现")
    for i, f in enumerate(findings, 1):
        strength = f.get("evidence_strength", "unknown")
        lines.append(f"### {i}. {f.get('title', '')}（{strength}）")
        lines.append(f"> {f.get('description', '')}")
        if f.get("suggested_action"):
            lines.append(f"- **建议**：{f['suggested_action']}")
        quotes = f.get("representative_quotes") or []
        for q in quotes[:2]:
            lines.append(f"  - \"{q[:150]}\"")
        lines.append("")
    lines.append("## PRD 需求")
    for r in prd_requirements:
        lines.append(f"- [{r.get('priority','-')}/{r.get('version_suggestion','-')}] **{r.get('title','')}** — {r.get('user_story','')}")
    lines.append("")
    lines.append("## 测试用例")
    for t in test_cases:
        lines.append(f"- [{t.get('type','')}] {t.get('title','')} → Given: {t.get('given','')}, When: {t.get('when','')}, Then: {t.get('then','')}")
    text = "\n".join(lines)
    if filepath:
        _ensure_dir(filepath)
        with open(filepath, "w", encoding="utf-8") as fp:
            fp.write(text)
    return text


def export_testcases_csv(test_cases: list, filepath: str = None) -> str:
    """导出测试用例为 CSV 字符串；若指定 filepath 同时写入文件"""
    buf = io.StringIO()
    fieldnames = ["requirement_id", "title", "preconditions", "given", "when", "then", "type"]
    if test_cases:
        keys = list(test_cases[0].keys())
        for k in keys:
            if k not in fieldnames:
                fieldnames.append(k)
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for t in test_cases:
        row = {k: t.get(k, "") for k in fieldnames}
        writer.writerow(row)
    text = buf.getvalue()
    if filepath:
        _ensure_dir(filepath)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
    return text


# 兼容别名
export_test_cases_csv = export_testcases_csv
