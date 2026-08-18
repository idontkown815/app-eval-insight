import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.orchestrator import PipelineOrchestrator


def generate_dummy_reviews(count: int = 10) -> list:
    reviews = []
    ratings = [1, 2, 3, 4, 5, 1, 2, 4, 5, 3]
    contents = [
        "This app crashes every time I open it! Very frustrating experience, the crash happens within seconds of launch. I have tried reinstalling multiple times with no success.",
        "Serious login issues, cannot access my account. Password reset not working, the emails never arrive. Support hasn't responded to my tickets in 3 days.",
        "It's an okay app overall, does what it's supposed to do. Nothing amazing but also nothing terrible. Average performance and features.",
        "Great app for staying connected with friends! The interface is intuitive and features are well designed. I use it multiple times every day.",
        "Absolutely love this platform! The new features are amazing and make sharing content so easy. Perfect design and great user experience overall.",
        "Too many ads everywhere! I see an ad every 3 posts, it's ruining the experience. The app also feels slow and broken when ads are loading.",
        "The video playback keeps freezing constantly. I have to close the app and reopen it to fix it. The freeze issue happens on all video content.",
        "Battery drain is really bad with this version. My phone dies within 3 hours of light usage. Also getting hot while just scrolling through feed.",
        "Excellent user experience and feature set! The photo tools are easy to use yet powerful. Great for staying in touch with family and friends.",
        "Normal application experience. Not bad but could definitely be better. I use it out of habit more than actual enjoyment these days."
    ]
    titles = [
        "Constant crashes",
        "Cannot login at all",
        "Just okay",
        "Great social app",
        "Love it!",
        "Too many ads",
        "Video playback broken",
        "Battery drain problem",
        "Excellent features",
        "Average experience"
    ]
    versions = ["450", "451", "452", "453", "453", "452", "451", "453", "452", "450"]

    for i in range(count):
        review_date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        reviews.append({
            "review_id": f"r_smoke_{i+1:03d}",
            "author": f"SmokeUser{i+1:02d}",
            "rating": ratings[i],
            "title": titles[i],
            "content": contents[i],
            "review_date": review_date,
            "version": versions[i]
        })
    return reviews


def main():
    print("=" * 70)
    print("FALLBACK MODE SMOKE TEST - 离线降级模式冒烟测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()

    step_results = {}
    all_passed = True

    try:
        print("[Step 1/10] 初始化 PipelineOrchestrator")
        print("-" * 70)
        orchestrator = PipelineOrchestrator()
        print(f"  PipelineOrchestrator 初始化成功")
        print(f"  LLM 可用状态: {orchestrator.llm_client.is_available()}")
        print(f"  预期结果: LLM 不可用 (使用 fallback 降级模式)")
        if orchestrator.llm_client.is_available():
            print("  警告: LLM 已配置，本次测试仍将手动调用 fallback 方法")
        print("  [PASS]")
        print()
        step_results["Step1_Init"] = "PASS"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step1_Init"] = f"FAIL: {e}"
        print()

    try:
        print("[Step 2/10] 构造 dummy reviews 列表 (10条)")
        print("-" * 70)
        dummy_reviews = generate_dummy_reviews(10)
        print(f"  生成评价数量: {len(dummy_reviews)}")
        ratings_dist = {}
        for r in dummy_reviews:
            rt = r["rating"]
            ratings_dist[rt] = ratings_dist.get(rt, 0) + 1
        print(f"  评分分布: {dict(sorted(ratings_dist.items()))}")
        assert len(dummy_reviews) == 10, "评价数量应该为10"
        print("  [PASS]")
        print()
        step_results["Step2_DummyReviews"] = f"PASS (count={len(dummy_reviews)})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step2_DummyReviews"] = f"FAIL: {e}"
        print()

    try:
        print("[Step 3/10] 运行 GoalUnderstander.understand (无 LLM，返回默认目标)")
        print("-" * 70)
        goal_analysis = orchestrator.goal_understander.understand("")
        print(f"  focus_areas 数量: {len(goal_analysis.get('focus_areas', []))}")
        print(f"  focus_areas: {goal_analysis.get('focus_areas')}")
        print(f"  analysis_intents 数量: {len(goal_analysis.get('analysis_intents', []))}")
        print(f"  analysis_intents: {goal_analysis.get('analysis_intents')}")
        assert "focus_areas" in goal_analysis, "缺少 focus_areas 字段"
        assert "analysis_intents" in goal_analysis, "缺少 analysis_intents 字段"
        print("  [PASS]")
        print()
        step_results["Step3_GoalUnderstander"] = f"PASS (focus={len(goal_analysis.get('focus_areas', []))}, intents={len(goal_analysis.get('analysis_intents', []))})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step3_GoalUnderstander"] = f"FAIL: {e}"
        print()

    try:
        print("[Step 4/10] 运行 DynamicClassifier._fallback_classify (分3类)")
        print("-" * 70)
        focus_areas = goal_analysis.get("focus_areas", ["全面分析"])
        categories = orchestrator.classifier._fallback_classify(dummy_reviews, focus_areas)
        print(f"  分类数量: {len(categories)}")
        for cat in categories:
            name = cat.get("name", "")
            count = len(cat.get("review_ids", []))
            sentiment = cat.get("sentiment", "")
            print(f"    - {name}: {count} 条, 情感={sentiment}")
        assert len(categories) <= 3, "fallback 分类最多 3 类 (正/中/负)"
        assert len(categories) >= 1, "至少应有 1 个分类"
        print("  [PASS]")
        print()
        step_results["Step4_Classifier"] = f"PASS (categories={len(categories)})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step4_Classifier"] = f"FAIL: {e}"
        categories = []
        print()

    try:
        print("[Step 5/10] 运行 FindingGenerator._fallback_findings")
        print("-" * 70)
        findings = orchestrator.finding_generator._fallback_findings(categories, dummy_reviews)
        print(f"  发现数量: {len(findings)}")
        for idx, f in enumerate(findings):
            title = f.get("title", "")
            strength = f.get("evidence_strength", "")
            support_count = len(f.get("supporting_review_ids", []))
            is_positive = f.get("is_positive", None)
            print(f"    [{idx+1}] {title[:40]}... | strength={strength} | 支撑数={support_count} | positive={is_positive}")
        assert len(findings) <= 5, "fallback findings 最多5条"
        print("  [PASS]")
        print()
        step_results["Step5_FindingGenerator"] = f"PASS (findings={len(findings)})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step5_FindingGenerator"] = f"FAIL: {e}"
        findings = []
        print()

    try:
        print("[Step 6/10] 运行 EvidenceEvaluator.evaluate")
        print("-" * 70)
        evaluated_findings = orchestrator.evidence_evaluator.evaluate(findings, dummy_reviews)
        print(f"  评估后的发现数量: {len(evaluated_findings)}")
        strength_counts = {}
        hypothesis_count = 0
        contradictory_count = 0
        for idx, f in enumerate(evaluated_findings):
            strength = f.get("evidence_strength", "unknown")
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
            is_hypo = f.get("is_hypothesis", False)
            is_contr = f.get("is_contradictory", False)
            if is_hypo:
                hypothesis_count += 1
            if is_contr:
                contradictory_count += 1
            print(f"    [{idx+1}] strength={strength} | is_hypothesis={is_hypo} | contradictory={is_contr}")
        print(f"  证据强度分布: {strength_counts}")
        print(f"  假设数量 (证据不足3条): {hypothesis_count}")
        print(f"  存在矛盾的发现数量: {contradictory_count}")
        assert len(evaluated_findings) == len(findings), "评估后数量应与评估前一致"
        print("  [PASS]")
        print()
        step_results["Step6_EvidenceEvaluator"] = f"PASS (evaluated={len(evaluated_findings)}, hypothesis={hypothesis_count})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step6_EvidenceEvaluator"] = f"FAIL: {e}"
        evaluated_findings = []
        print()

    try:
        print("[Step 7/10] 运行 PRDGenerator._fallback_generate")
        print("-" * 70)
        prd_result = orchestrator.prd_generator._fallback_generate(evaluated_findings)
        requirements = prd_result.get("requirements", [])
        version_plan = prd_result.get("version_plan", {})
        print(f"  需求 (requirements) 数量: {len(requirements)}")
        priority_counts = {}
        version_counts = {}
        for idx, req in enumerate(requirements):
            rid = req.get("id", "")
            title = req.get("title", "")[:35]
            priority = req.get("priority", "")
            ver = req.get("version_suggestion", "")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            version_counts[ver] = version_counts.get(ver, 0) + 1
            print(f"    {rid}: {title}... | priority={priority} | version={ver}")
        print(f"  优先级分布: {priority_counts}")
        print(f"  版本分布: {version_counts}")
        print(f"  版本规划 (version_plan): {version_plan}")
        assert "requirements" in prd_result, "缺少 requirements 字段"
        assert "version_plan" in prd_result, "缺少 version_plan 字段"
        assert len(requirements) == len(evaluated_findings), "需求数应等于发现数"
        print("  [PASS]")
        print()
        step_results["Step7_PRDGenerator"] = f"PASS (requirements={len(requirements)}, priorities={priority_counts})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step7_PRDGenerator"] = f"FAIL: {e}"
        requirements = []
        print()

    try:
        print("[Step 8/10] 运行 TestCaseGenerator._fallback_generate")
        print("-" * 70)
        test_cases = orchestrator.test_case_generator._fallback_generate(requirements)
        print(f"  测试用例数量: {len(test_cases)}")
        type_counts = {}
        req_coverage = set()
        for idx, tc in enumerate(test_cases):
            req_id = tc.get("requirement_id", "")
            title = tc.get("title", "")[:40]
            tc_type = tc.get("type", "")
            type_counts[tc_type] = type_counts.get(tc_type, 0) + 1
            req_coverage.add(req_id)
            print(f"    [{idx+1}] {req_id} | {title}... | type={tc_type}")
        print(f"  用例类型分布: {type_counts}")
        print(f"  覆盖的需求数量: {len(req_coverage)}/{len(requirements)}")
        expected_count = len(requirements) * 2
        assert len(test_cases) == expected_count, f"每个需求应生成 2 条用例，期望 {expected_count} 条，实际 {len(test_cases)} 条"
        print("  [PASS]")
        print()
        step_results["Step8_TestCaseGenerator"] = f"PASS (test_cases={len(test_cases)}, types={type_counts})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step8_TestCaseGenerator"] = f"FAIL: {e}"
        test_cases = []
        print()

    try:
        print("[Step 9/10] 运行 TraceabilityChecker._rule_based_check")
        print("-" * 70)
        issues = orchestrator.traceability_checker._rule_based_check(
            dummy_reviews,
            evaluated_findings,
            requirements,
            test_cases
        )
        print(f"  发现问题 (issues) 数量: {len(issues)}")
        severity_counts = {}
        type_counts = {}
        for idx, issue in enumerate(issues):
            itype = issue.get("type", "")
            severity = issue.get("severity", "")
            desc = issue.get("description", "")[:50]
            location = issue.get("location", "")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[itype] = type_counts.get(itype, 0) + 1
            print(f"    [{idx+1}] [{severity.upper()}] {itype} @ {location}")
            print(f"         {desc}...")
        print(f"  严重程度分布: {severity_counts}")
        print(f"  问题类型分布: {type_counts}")
        print("  [PASS] - 方法正常返回 (即使发现问题也是正常行为)")
        print()
        step_results["Step9_TraceabilityChecker"] = f"PASS (issues={len(issues)}, severity={severity_counts})"
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step9_TraceabilityChecker"] = f"FAIL: {e}"
        issues = []
        print()

    try:
        print("[Step 10/10] 汇总结果验证 & 完整性检查")
        print("-" * 70)
        print("  检查数据链路完整性:")
        print(f"    原始评价 (reviews): {len(dummy_reviews)} 条")
        print(f"    分类结果 (categories): {len(categories)} 类")
        print(f"    关键发现 (findings): {len(evaluated_findings)} 条")
        print(f"    PRD需求 (requirements): {len(requirements)} 条")
        print(f"    测试用例 (test_cases): {len(test_cases)} 条")
        print(f"    追溯问题 (issues): {len(issues)} 个")
        print()

        print("  检查关键字段存在性:")
        checks_passed = 0
        total_checks = 0

        if dummy_reviews and len(dummy_reviews) > 0:
            r0 = dummy_reviews[0]
            for field in ["review_id", "author", "rating", "content", "review_date", "version"]:
                total_checks += 1
                if field in r0:
                    checks_passed += 1
                    print(f"    [OK] review.{field} 存在")
                else:
                    print(f"    [MISS] review.{field} 缺失")

        if evaluated_findings and len(evaluated_findings) > 0:
            f0 = evaluated_findings[0]
            for field in ["title", "description", "evidence_strength", "supporting_review_ids", "is_positive"]:
                total_checks += 1
                if field in f0:
                    checks_passed += 1
                    print(f"    [OK] finding.{field} 存在")
                else:
                    print(f"    [MISS] finding.{field} 缺失")

        if requirements and len(requirements) > 0:
            rq0 = requirements[0]
            for field in ["id", "finding_id", "title", "user_story", "priority", "version_suggestion"]:
                total_checks += 1
                if field in rq0:
                    checks_passed += 1
                    print(f"    [OK] requirement.{field} 存在")
                else:
                    print(f"    [MISS] requirement.{field} 缺失")

        if test_cases and len(test_cases) > 0:
            tc0 = test_cases[0]
            for field in ["requirement_id", "title", "preconditions", "given", "when", "then", "type"]:
                total_checks += 1
                if field in tc0:
                    checks_passed += 1
                    print(f"    [OK] test_case.{field} 存在")
                else:
                    print(f"    [MISS] test_case.{field} 缺失")

        print(f"  字段检查结果: {checks_passed}/{total_checks} 通过")

        if all_passed and checks_passed == total_checks:
            print("  [PASS] 完整验证通过")
            step_results["Step10_Summary"] = f"PASS (fields={checks_passed}/{total_checks})"
        else:
            if checks_passed != total_checks:
                all_passed = False
            print("  [FAIL] 存在未通过项")
            step_results["Step10_Summary"] = f"FAIL (fields={checks_passed}/{total_checks})"
        print()

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        all_passed = False
        step_results["Step10_Summary"] = f"FAIL: {e}"
        print()

    print("=" * 70)
    print("测试结果汇总 (Summary)")
    print("=" * 70)
    for step_name, result in step_results.items():
        status_char = "✓" if result.startswith("PASS") else "✗"
        print(f"  {status_char} {step_name}: {result}")
    print()

    print("=" * 70)
    if all_passed:
        print("🎉 全部步骤通过！Fallback 降级模式完整可运行")
    else:
        print("⚠️  存在失败步骤，请检查上述报错信息")
    print(f"结束时间: {datetime.now().isoformat()}")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
