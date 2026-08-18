import { useState } from 'react'
import {
  AppInfo, TaskResults, Category, Finding, Requirement, TestCase, Verification
} from '../types'
import { exportResults } from '../api/client'
import {
  Download, FileText, CheckCircle2, AlertTriangle, XCircle,
  Lightbulb, ListChecks, ShieldCheck, ThumbsUp, ThumbsDown,
  ChevronDown, ChevronRight, Tag, Clock
} from 'lucide-react'

interface Props {
  taskId: string
  results: TaskResults
  appInfo: AppInfo | null
  userGoal: string
}

type Tab = 'overview' | 'categories' | 'findings' | 'prd' | 'tests' | 'verification'

const TABS: { id: Tab; label: string; icon: any }[] = [
  { id: 'overview', label: '总览', icon: FileText },
  { id: 'categories', label: '评价分类', icon: Tag },
  { id: 'findings', label: '关键发现', icon: Lightbulb },
  { id: 'prd', label: 'PRD 需求', icon: ListChecks },
  { id: 'tests', label: '测试用例', icon: ShieldCheck },
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
      </div>
      <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100">
        <span className="font-medium">用户故事：</span>{req.user_story}
      </p>
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
