import { useState } from 'react'
import {
  AppInfo, TaskResults, Category, Finding, Requirement, TestCase, Verification
} from '../types'
import { exportResults } from '../api/client'
import {
  Download, FileText, CheckCircle2, AlertTriangle, XCircle,
  Lightbulb, ListChecks, ShieldCheck, ThumbsUp, ThumbsDown,
  ChevronDown, ChevronRight, Tag, Clock, Database, GitBranch, Cpu, Globe
} from 'lucide-react'

interface Props {
  taskId: string
  results: TaskResults
  appInfo: AppInfo | null
  userGoal: string
}

type Tab = 'overview' | 'categories' | 'findings' | 'prd' | 'tests' | 'verification' | 'traceability'

const TABS: { id: Tab; label: string; icon: any }[] = [
  { id: 'overview', label: '总览', icon: FileText },
  { id: 'categories', label: '评价分类', icon: Tag },
  { id: 'findings', label: '关键发现', icon: Lightbulb },
  { id: 'prd', label: 'PRD 需求', icon: ListChecks },
  { id: 'tests', label: '测试用例', icon: ShieldCheck },
  { id: 'traceability', label: '追溯链', icon: GitBranch },
  { id: 'verification', label: '验证报告', icon: CheckCircle2 },
]

const EVIDENCE_STYLE = {
  strong: 'bg-green-100 text-green-700 border-green-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  weak: 'bg-gray-100 text-gray-600 border-gray-200',
}

const PRIORITY_STYLE = {
  P0: 'bg-red-100 text-red-700 border-red-200',
  P1: 'bg-orange-100 text-orange-700 border-orange-200',
  P2: 'bg-blue-100 text-blue-700 border-blue-200',
}

const SEVERITY_STYLE = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-blue-100 text-blue-700',
}

const SENTIMENT_STYLE = {
  positive: 'bg-green-50 text-green-700 border-green-200',
  negative: 'bg-red-50 text-red-700 border-red-200',
  neutral: 'bg-gray-50 text-gray-600 border-gray-200',
  mixed: 'bg-purple-50 text-purple-700 border-purple-200',
}

export default function ResultPanel({ taskId, results, appInfo, userGoal }: Props) {
  const [tab, setTab] = useState<Tab>('overview')
  const [expandedFindings, setExpandedFindings] = useState<Set<number>>(new Set())
  const [exporting, setExporting] = useState<string | null>(null)

  const toggleFinding = (id: number) => {
    const next = new Set(expandedFindings)
    if (next.has(id)) next.delete(id); else next.add(id)
    setExpandedFindings(next)
  }

  const handleExport = async (format: 'csv' | 'md' | 'json') => {
    setExporting(format)
    try {
      const blob = await exportResults(taskId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `result-${taskId.slice(0, 8)}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('导出失败', e)
    } finally {
      setExporting(null)
    }
  }

  const totalReviews = results.cleaned_reviews?.length || 0
  const categoryCount = results.categories?.length || 0
  const findingCount = results.findings?.length || 0
  const positiveFindings = results.findings?.filter(f => f.is_positive).length || 0
  const negativeFindings = findingCount - positiveFindings
  const requirementCount = results.prd?.requirements?.length || 0
  const testCaseCount = results.test_cases?.length || 0

  return (
    <div className="w-full fade-in">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            {appInfo?.icon_url && <img src={appInfo.icon_url} className="w-16 h-16 rounded-2xl" />}
            <div>
              <h2 className="text-xl font-bold">{appInfo?.name || '未知应用'}</h2>
              <p className="text-sm text-gray-600">{appInfo?.developer} · {appInfo?.category}</p>
              <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                <span>评分 {Number(appInfo?.rating || 0).toFixed(1)}</span>
                <span>任务 ID：{taskId.slice(0, 8)}...</span>
                {results.is_fallback && (
                  <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">降级分析</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport('json')}
              disabled={!!exporting}
              className="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {exporting === 'json' ? '导出中...' : 'JSON'}
            </button>
            <button
              onClick={() => handleExport('md')}
              disabled={!!exporting}
              className="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {exporting === 'md' ? '导出中...' : 'Markdown'}
            </button>
            <button
              onClick={() => handleExport('csv')}
              disabled={!!exporting}
              className="flex items-center gap-1.5 px-3 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {exporting === 'csv' ? '导出中...' : '导出 CSV'}
            </button>
          </div>
        </div>
        {userGoal && (
          <div className="mt-5 p-4 bg-gray-50 rounded-xl border border-gray-100">
            <p className="text-xs text-gray-500 mb-1">🎯 分析目标</p>
            <p className="text-sm text-gray-800">{userGoal}</p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 mb-6 overflow-hidden">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-5 py-3 text-sm font-medium whitespace-nowrap transition ${
                tab === t.id
                  ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {tab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="清洗后评价" value={totalReviews} color="blue" />
                <StatCard label="分类数" value={categoryCount} color="purple" />
                <StatCard label="关键发现" value={findingCount} sub={`${positiveFindings} 正面 / ${negativeFindings} 待改进`} color="green" />
                <StatCard label="测试用例" value={testCaseCount} sub={`${requirementCount} 条需求`} color="orange" />
              </div>

              {/* 数据来源与局限性透明说明 */}
              <Section title="📊 数据来源与局限性" desc="真实数据来源、采集方式和已知局限">
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <Database className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-800">{results.data_fetch_note || '数据来源未记录'}</p>
                      {results.data_source === 'cache' && (
                        <p className="text-xs text-amber-600 mt-1">⚠ 当前使用缓存数据，可能已过期</p>
                      )}
                    </div>
                  </div>

                  {/* 清洗报告 */}
                  {results.cleaning_report && (
                    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <FileText className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 text-sm">
                        <div className="flex flex-wrap gap-3 text-gray-700">
                          <span>原始：<b>{results.cleaning_report.original_count}</b> 条</span>
                          <span>清洗后：<b className="text-blue-600">{results.cleaning_report.cleaned_count}</b> 条</span>
                          <span>移除：<b className="text-red-500">{results.cleaning_report.removed_count}</b> 条</span>
                          {results.cleaning_report.duplicate_content_removed > 0 && (
                            <span>内容重复：<b className="text-orange-500">{results.cleaning_report.duplicate_content_removed}</b> 条</span>
                          )}
                        </div>
                        {results.cleaning_report.has_mixed_languages && (
                          <div className="mt-2 flex items-center gap-2 text-xs text-purple-600">
                            <Globe className="w-3.5 h-3.5" />
                            检测到混合语言：
                            {Object.entries(results.cleaning_report.language_distribution || {}).map(([lang, count]) => (
                              <span key={lang} className="px-1.5 py-0.5 bg-purple-100 rounded">{lang}: {count as number}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* LLM / 规则模式标记 */}
                  <div className="flex items-start gap-3 p-3 rounded-lg border ${
                    results.llm_available === false ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'
                  }" style={{ background: results.llm_available === false ? '#fffbeb' : '#f0fdf4', borderColor: results.llm_available === false ? '#fde68a' : '#bbf7d0' }}>
                    <Cpu className={`w-5 h-5 flex-shrink-0 mt-0.5 ${results.llm_available === false ? 'text-amber-500' : 'text-green-500'}`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">
                        {results.llm_available === false
                          ? '⚠ 当前为规则降级模式（未配置 LLM API Key）'
                          : '✓ 模型驱动语义分析已启用'}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {results.llm_available === false
                          ? '分类、发现、PRD、测试用例均由规则引擎生成。请在 .env 中配置 LLM_API_KEY 以启用 AI 语义分析。'
                          : `使用 LLM 模型进行分析，每个结果项标注了生成方式（LLM/规则）。`}
                      </p>
                      {results.is_fallback && (
                        <p className="text-xs text-amber-600 mt-1">部分分析因 LLM 异常降级为规则</p>
                      )}
                    </div>
                  </div>
                </div>
              </Section>

              {results.goal_analysis && (
                <Section title="🎯 目标分析" desc="根据分析目标自动识别的关注方向">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">关注领域</p>
                      <div className="flex flex-wrap gap-2">
                        {results.goal_analysis.focus_areas.map((a, i) => (
                          <span key={i} className="px-2.5 py-1 text-xs bg-primary-50 text-primary-700 rounded-full">{a}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">分析意图</p>
                      <div className="flex flex-wrap gap-2">
                        {results.goal_analysis.analysis_intents.map((a, i) => (
                          <span key={i} className="px-2.5 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-full">{a}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </Section>
              )}

              {results.verification && (
                <Section title="✅ 整体验证状态" desc="追溯链完整性验证">
                  <div className={`p-4 rounded-xl border ${
                    results.verification.overall_status === 'pass'
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      {results.verification.overall_status === 'pass'
                        ? <CheckCircle2 className="w-5 h-5 text-green-600" />
                        : <XCircle className="w-5 h-5 text-red-600" />}
                      <span className="font-semibold">
                        {results.verification.overall_status === 'pass' ? '验证通过' : '存在问题'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{results.verification.summary}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      通过项：{results.verification.passed.length} · 问题数：{results.verification.issues.length}
                    </p>
                  </div>
                </Section>
              )}
            </div>
          )}

          {tab === 'categories' && (
            <div className="grid md:grid-cols-2 gap-4">
              {results.categories?.map((c, i) => (
                <CategoryCard key={i} cat={c} />
              ))}
              {!results.categories?.length && <EmptyState text="暂无分类数据" />}
            </div>
          )}

          {tab === 'findings' && (
            <div className="space-y-3">
              {results.findings?.map((f, i) => (
                <FindingCard
                  key={f.id ?? i}
                  finding={f}
                  expanded={expandedFindings.has(f.id ?? i)}
                  onToggle={() => toggleFinding(f.id ?? i)}
                />
              ))}
              {!results.findings?.length && <EmptyState text="暂无关键发现" />}
            </div>
          )}

          {tab === 'prd' && (
            <div className="space-y-4">
              {results.prd?.version_plan && (
                <Section title="📋 版本规划">
                  <pre className="text-xs bg-gray-50 p-4 rounded-xl overflow-x-auto">
                    {JSON.stringify(results.prd.version_plan, null, 2)}
                  </pre>
                </Section>
              )}
              <div className="space-y-3">
                {results.prd?.requirements?.map(r => (
                  <RequirementCard key={r.id} req={r} />
                ))}
                {!results.prd?.requirements?.length && <EmptyState text="暂无需求" />}
              </div>
            </div>
          )}

          {tab === 'tests' && (
            <div className="space-y-3">
              {results.test_cases?.map((t, i) => (
                <TestCaseCard key={t.id ?? i} tc={t} />
              ))}
              {!results.test_cases?.length && <EmptyState text="暂无测试用例" />}
            </div>
          )}

          {tab === 'traceability' && (
            <TraceabilityView results={results} />
          )}

          {tab === 'verification' && (
            results.verification ? (
              <VerificationBlock v={results.verification} />
            ) : <EmptyState text="暂无验证报告" />
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, color }: { label: string; value: number; sub?: string; color: string }) {
  const colors: Record<string, string> = {
    blue: 'from-blue-50 to-blue-100 text-blue-700 border-blue-200',
    purple: 'from-purple-50 to-purple-100 text-purple-700 border-purple-200',
    green: 'from-green-50 to-green-100 text-green-700 border-green-200',
    orange: 'from-orange-50 to-orange-100 text-orange-700 border-orange-200',
  }
  return (
    <div className={`p-4 rounded-xl bg-gradient-to-br border ${colors[color] || colors.blue}`}>
      <p className="text-xs opacity-80 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value.toLocaleString()}</p>
      {sub && <p className="text-xs mt-1 opacity-70">{sub}</p>}
    </div>
  )
}

function Section({ title, desc, children }: { title: string; desc?: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {desc && <p className="text-xs text-gray-500 mt-0.5">{desc}</p>}
      </div>
      {children}
    </div>
  )
}

function CategoryCard({ cat }: { cat: Category }) {
  const sentimentStyle = SENTIMENT_STYLE[cat.sentiment || 'neutral']
  return (
    <div className="p-4 rounded-xl border border-gray-200 hover:border-gray-300 transition">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-gray-500" />
          <h4 className="font-semibold text-gray-900">{cat.name}</h4>
        </div>
        {cat.sentiment && (
          <span className={`text-xs px-2 py-0.5 rounded-full border ${sentimentStyle}`}>
            {cat.sentiment === 'positive' ? '正面' : cat.sentiment === 'negative' ? '负面' : cat.sentiment === 'mixed' ? '混合' : '中性'}
          </span>
        )}
      </div>
      {cat.description && <p className="text-sm text-gray-600 mb-2">{cat.description}</p>}
      <p className="text-xs text-gray-500 mb-2">{cat.review_ids.length} 条评价</p>
      {cat.key_points && cat.key_points.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {cat.key_points.map((k, i) => (
            <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded">{k}</span>
          ))}
        </div>
      )}
    </div>
  )
}

function FindingCard({ finding, expanded, onToggle }: { finding: Finding; expanded: boolean; onToggle: () => void }) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden hover:border-gray-300 transition">
      <button onClick={onToggle} className="w-full p-4 text-left flex items-start gap-3">
        <div className="mt-0.5 flex-shrink-0">
          {expanded ? <ChevronDown className="w-5 h-5 text-gray-500" /> : <ChevronRight className="w-5 h-5 text-gray-500" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            {finding.is_positive ? (
              <ThumbsUp className="w-4 h-4 text-green-600" />
            ) : (
              <ThumbsDown className="w-4 h-4 text-red-500" />
            )}
            <h4 className="font-semibold text-gray-900">{finding.title}</h4>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${EVIDENCE_STYLE[finding.evidence_strength]}`}>
              证据{finding.evidence_strength === 'strong' ? '强' : finding.evidence_strength === 'medium' ? '中' : '弱'}
            </span>
            {finding.is_hypothesis && <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">假设</span>}
            {finding.is_contradictory && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">矛盾</span>}
            <GeneratedByBadge by={finding.generated_by} />
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">{finding.description}</p>
          <p className="text-xs text-gray-500 mt-2">{finding.supporting_review_ids.length} 条支持评价</p>
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100 ml-8">
          {finding.representative_quotes && finding.representative_quotes.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-700 mb-2">📝 代表性引用</p>
              <div className="space-y-2">
                {finding.representative_quotes.map((q, i) => (
                  <blockquote key={i} className="text-sm text-gray-700 italic bg-gray-50 p-3 rounded-lg border-l-4 border-primary-400">
                    "{q}"
                  </blockquote>
                ))}
              </div>
            </div>
          )}
          {finding.suggested_action && (
            <div className="mt-3 p-3 bg-primary-50 rounded-lg border border-primary-100">
              <p className="text-xs font-medium text-primary-700 mb-1">💡 建议行动</p>
              <p className="text-sm text-primary-900">{finding.suggested_action}</p>
            </div>
          )}
          {finding.data_limitation && (
            <div className="mt-3 p-3 bg-yellow-50 rounded-lg border border-yellow-100">
              <p className="text-xs font-medium text-yellow-700 mb-1">⚠️ 数据局限</p>
              <p className="text-sm text-yellow-900">{finding.data_limitation}</p>
            </div>
          )}
          {finding.conflict_detail && (
            <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-xs font-medium text-amber-700 mb-1">⚠️ 矛盾反馈</p>
              <p className="text-sm text-amber-900">{finding.conflict_detail}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RequirementCard({ req }: { req: Requirement }) {
  return (
    <div className="p-4 rounded-xl border border-gray-200">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-xs font-mono px-2 py-0.5 bg-gray-100 rounded">{req.id}</span>
        <h4 className="font-semibold text-gray-900">{req.title}</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full border ${PRIORITY_STYLE[req.priority]}`}>{req.priority}</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200">{req.version_suggestion}</span>
        {req.finding_id != null && (
          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">关联发现 #{req.finding_id}</span>
        )}
        <GeneratedByBadge by={req.generated_by} />
      </div>
      <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100">
        <span className="font-medium">用户故事：</span>{req.user_story}
      </p>
      {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
        <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-xs font-medium text-blue-700 mb-1">验收标准</p>
          <ul className="space-y-1">
            {req.acceptance_criteria.map((c, i) => (
              <li key={i} className="text-xs text-gray-700 flex items-start gap-1">
                <span className="text-blue-500 flex-shrink-0">✓</span> {c}
              </li>
            ))}
          </ul>
        </div>
      )}
      {req.source_review_ids && req.source_review_ids.length > 0 && (
        <p className="text-xs text-gray-500 mt-2">追溯至 {req.source_review_ids.length} 条用户评价</p>
      )}
    </div>
  )
}

function TestCaseCard({ tc }: { tc: TestCase }) {
  return (
    <div className="p-4 rounded-xl border border-gray-200">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          tc.type === 'positive' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {tc.type === 'positive' ? '正向测试' : '反向测试'}
        </span>
        <span className="text-xs font-mono px-2 py-0.5 bg-gray-100 rounded">需求: {tc.requirement_id}</span>
        <h4 className="font-semibold text-gray-900 flex-1">{tc.title}</h4>
        <GeneratedByBadge by={tc.generated_by} />
      </div>
      <div className="grid gap-2 text-sm">
        {tc.preconditions && (
          <div className="flex gap-2">
            <span className="text-xs font-medium text-gray-500 w-24 flex-shrink-0 flex items-center gap-1">
              <Clock className="w-3 h-3" />前置条件
            </span>
            <span className="text-gray-700 bg-gray-50 p-2 rounded flex-1">{tc.preconditions}</span>
          </div>
        )}
        <div className="flex gap-2">
          <span className="text-xs font-medium text-gray-500 w-24 flex-shrink-0">Given</span>
          <span className="text-gray-700 bg-blue-50 p-2 rounded flex-1">{tc.given}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-xs font-medium text-gray-500 w-24 flex-shrink-0">When</span>
          <span className="text-gray-700 bg-yellow-50 p-2 rounded flex-1">{tc.when}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-xs font-medium text-gray-500 w-24 flex-shrink-0">Then</span>
          <span className="text-gray-700 bg-green-50 p-2 rounded flex-1">{tc.then}</span>
        </div>
        {tc.source_review_ids && tc.source_review_ids.length > 0 && (
          <div className="flex gap-2">
            <span className="text-xs font-medium text-gray-500 w-24 flex-shrink-0">追溯</span>
            <span className="text-xs text-gray-500 flex-1">来自 {tc.source_review_ids.length} 条用户评价</span>
          </div>
        )}
      </div>
    </div>
  )
}

function VerificationBlock({ v }: { v: Verification }) {
  return (
    <div className="space-y-4">
      <div className={`p-4 rounded-xl border ${
        v.overall_status === 'pass' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          {v.overall_status === 'pass'
            ? <CheckCircle2 className="w-6 h-6 text-green-600" />
            : <XCircle className="w-6 h-6 text-red-600" />}
          <h3 className="text-lg font-bold">{v.overall_status === 'pass' ? '整体验证通过' : '发现验证问题'}</h3>
        </div>
        <p className="text-gray-700">{v.summary}</p>
      </div>

      {v.passed.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2 flex items-center gap-2 text-green-700">
            <CheckCircle2 className="w-4 h-4" /> 通过项 ({v.passed.length})
          </h4>
          <ul className="space-y-1">
            {v.passed.map((p, i) => (
              <li key={i} className="text-sm text-gray-700 pl-6 relative">
                <CheckCircle2 className="w-4 h-4 absolute left-0 top-0.5 text-green-500" />
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {v.issues.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2 flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-4 h-4" /> 问题项 ({v.issues.length})
          </h4>
          <div className="space-y-2">
            {v.issues.map((iss, i) => (
              <div key={i} className="p-3 rounded-lg border border-gray-200 flex items-start gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${SEVERITY_STYLE[iss.severity]}`}>
                  {iss.severity === 'high' ? '严重' : iss.severity === 'medium' ? '中等' : '轻微'}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-gray-800">{iss.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {iss.finding_id != null && `发现 #${iss.finding_id}`}
                    {iss.requirement_id && ` · 需求 ${iss.requirement_id}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="py-16 text-center text-gray-400 text-sm">{text}</div>
  )
}

function GeneratedByBadge({ by }: { by?: string }) {
  if (!by) return null
  const isLLM = by === 'llm'
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
      isLLM ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'
    }`}>
      {isLLM ? 'AI' : '规则'}
    </span>
  )
}

function TraceabilityView({ results }: { results: TaskResults }) {
  const reviews = results.cleaned_reviews || []
  const reviewMap = new Map(reviews.map(r => [r.review_id, r]))
  const findings = results.findings || []
  const requirements = results.prd?.requirements || []
  const testCases = results.test_cases || []

  return (
    <div className="space-y-4">
      <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
        <div className="flex items-center gap-2 mb-2">
          <GitBranch className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-blue-900">追溯链：评价 → 发现 → 需求 → 测试用例</h3>
        </div>
        <p className="text-sm text-blue-700">
          展示从用户评价到测试用例的完整追溯链。每条需求可追溯到具体的用户评价，确保产品决策基于真实用户反馈。
        </p>
      </div>

      {requirements.map((req) => {
        const finding = findings.find((f, i) => {
          const fid = f.id ?? i
          return String(fid) === String(req.finding_id)
        })
        const findingReviewIds = finding?.supporting_review_ids || []
        const reqReviewIds = req.source_review_ids || findingReviewIds
        const linkedTestCases = testCases.filter(tc => tc.requirement_id === req.id)

        return (
          <div key={req.id} className="border border-gray-200 rounded-xl overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono px-2 py-0.5 bg-gray-200 rounded">{req.id}</span>
                <span className="font-semibold text-gray-900">{req.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${PRIORITY_STYLE[req.priority]}`}>{req.priority}</span>
                <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">{req.version_suggestion}</span>
                <GeneratedByBadge by={req.generated_by} />
              </div>
            </div>

            <div className="p-4 space-y-3">
              {/* 追溯到发现 */}
              {finding && (
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">关键发现</p>
                    <p className="text-sm text-gray-800">{finding.title}</p>
                    <div className="flex gap-2 mt-1">
                      <span className={`text-xs px-1.5 py-0.5 rounded-full border ${EVIDENCE_STYLE[finding.evidence_strength]}`}>
                        证据{finding.evidence_strength === 'strong' ? '强' : finding.evidence_strength === 'medium' ? '中' : '弱'}
                      </span>
                      {finding.is_contradictory && <span className="text-xs px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700">矛盾</span>}
                      <GeneratedByBadge by={finding.generated_by} />
                    </div>
                  </div>
                </div>
              )}

              {/* 追溯到原始评价 */}
              {reqReviewIds.length > 0 && (
                <div className="flex items-start gap-2">
                  <FileText className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">来源用户评价（{reqReviewIds.length} 条）</p>
                    <div className="space-y-1 mt-1">
                      {reqReviewIds.slice(0, 3).map((rid, i) => {
                        const review = reviewMap.get(rid)
                        return (
                          <div key={i} className="text-xs p-2 bg-gray-50 rounded border-l-2 border-blue-400">
                            {review ? (
                              <>
                                <span className="text-gray-500">[{review.rating}★]</span>{' '}
                                <span className="text-gray-700">{review.content?.slice(0, 120)}{review.content?.length > 120 ? '...' : ''}</span>
                                {review.language && review.language !== 'en' && (
                                  <span className="ml-1 px-1 py-0.5 bg-purple-100 text-purple-600 rounded text-[10px]">{review.language}</span>
                                )}
                              </>
                            ) : (
                              <span className="text-gray-400">评价 ID: {rid}</span>
                            )}
                          </div>
                        )
                      })}
                      {reqReviewIds.length > 3 && <p className="text-xs text-gray-400">... 还有 {reqReviewIds.length - 3} 条</p>}
                    </div>
                  </div>
                </div>
              )}

              {/* 追溯到测试用例 */}
              {linkedTestCases.length > 0 && (
                <div className="flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">关联测试用例（{linkedTestCases.length} 条）</p>
                    <div className="space-y-1 mt-1">
                      {linkedTestCases.map((tc, i) => (
                        <div key={i} className="text-xs p-2 bg-green-50 rounded border-l-2 border-green-400">
                          <span className={`px-1.5 py-0.5 rounded ${tc.type === 'positive' ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'}`}>
                            {tc.type === 'positive' ? '正向' : '反向'}
                          </span>{' '}
                          <span className="text-gray-700">{tc.title}</span>
                          <GeneratedByBadge by={tc.generated_by} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* 验收标准 */}
              {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">验收标准</p>
                    <ul className="mt-1 space-y-1">
                      {req.acceptance_criteria.map((c, i) => (
                        <li key={i} className="text-xs text-gray-700 flex items-start gap-1">
                          <span className="text-blue-500 flex-shrink-0">✓</span> {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {!requirements.length && <EmptyState text="暂无追溯链数据" />}
    </div>
  )
}
