import { useEffect, useState } from 'react'
import LinkInput from './components/LinkInput'
import GoalInput from './components/GoalInput'
import ProgressView from './components/ProgressView'
import ResultPanel from './components/ResultPanel'
import { createTask, getProgress, getResults } from './api/client'
import type { AppInfo, Progress, TaskResults } from './types'
import { BarChart3, Search, RefreshCw } from 'lucide-react'

type Stage = 'input' | 'progress' | 'result'

export default function App() {
  const [stage, setStage] = useState<Stage>('input')
  const [bundleId, setBundleId] = useState('')
  const [url, setUrl] = useState('')
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null)
  const [userGoal, setUserGoal] = useState('')
  const [taskId, setTaskId] = useState('')
  const [progress, setProgress] = useState<Progress | null>(null)
  const [results, setResults] = useState<TaskResults | null>(null)
  const [starting, setStarting] = useState(false)
  const [err, setErr] = useState('')

  const onValidLink = (bid: string, u: string, info: AppInfo) => {
    setBundleId(bid); setUrl(u); setAppInfo(info); setErr('')
  }

  const handleStart = async (goal: string) => {
    if (!bundleId || !appInfo) return
    setStarting(true); setErr(''); setUserGoal(goal)
    try {
      const res = await createTask({
        bundle_id: bundleId,
        url,
        app_info: appInfo,
        user_goal: goal,
        filters: {},
      })
      setTaskId(res.task_id)
      setStage('progress')
    } catch (e: any) {
      setErr(e?.response?.data?.detail || e.message || '启动分析失败')
    } finally {
      setStarting(false)
    }
  }

  // 进度轮询
  useEffect(() => {
    if (stage !== 'progress' || !taskId) return
    let alive = true
    let count = 0
    const tick = async () => {
      try {
        const p = await getProgress(taskId)
        if (!alive) return
        setProgress(p)
        count++
        if (p.progress_percent >= 100 || p.stages.every(s => s.status === 'completed' || s.status === 'failed')) {
          const r = await getResults(taskId)
          if (r && (r.status === 'completed' || r.status === 'failed')) {
            // 将 deliverables 展开，让 UI 兼容 result 根字段访问
            const d = r.deliverables || {}
            const flat: TaskResults = {
              task_id: r.task_id,
              status: r.status as any,
              app_info: d.app_info || r.app_info,
              goal_analysis: d.goal_analysis,
              categories: d.categories,
              findings: d.findings,
              prd: d.prd,
              test_cases: d.test_cases,
              verification: d.verification,
              cleaning_report: d.cleaning_report,
              cleaned_reviews: r.cleaned_reviews || [],
              is_fallback: r.is_fallback,
              data_source: r.data_source,
              error: r.error,
            }
            setResults(flat); setStage('result'); return
          }
        }
      } catch { /* ignore */ }
      setTimeout(tick, count < 30 ? 2000 : 4000)
    }
    tick()
    return () => { alive = false }
  }, [stage, taskId])

  const resetAll = () => {
    setStage('input'); setBundleId(''); setUrl(''); setAppInfo(null)
    setUserGoal(''); setTaskId(''); setProgress(null); setResults(null); setErr('')
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 bg-white/80 backdrop-blur-md border-b border-gray-200 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-primary-600" />
            <div>
              <h1 className="text-xl font-bold">App Review Insight</h1>
              <p className="text-xs text-gray-500">美国 App Store 评价智能分析平台</p>
            </div>
          </div>
          {(stage === 'progress' || stage === 'result') && (
            <button onClick={resetAll} className="text-sm flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
              <RefreshCw className="w-3.5 h-3.5" /> 新建分析
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {stage === 'input' && (
          <>
            <div className="text-center mb-10 fade-in">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium mb-4">
                <Search className="w-3 h-3" /> 智能分析引擎
              </div>
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-3">
                让用户评价驱动产品决策
              </h2>
              <p className="text-gray-600 max-w-xl mx-auto">
                输入 App Store 链接，一键完成数据采集、清洗、动态分类、关键发现挖掘，
                并自动输出 PRD 需求文档、测试用例与完整追溯链。
              </p>
            </div>
            <LinkInput onValid={onValidLink} />
            {appInfo && <GoalInput onStart={handleStart} loading={starting} />}
            {err && <div className="max-w-3xl mx-auto mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">{err}</div>}
          </>
        )}

        {stage === 'progress' && progress && (
          <>
            <div className="mb-6 flex items-center justify-between max-w-3xl mx-auto">
              <div className="flex items-center gap-3">
                {appInfo?.icon_url && <img src={appInfo.icon_url} className="w-12 h-12 rounded-xl" />}
                <div>
                  <h3 className="font-semibold">{appInfo?.name}</h3>
                  <p className="text-xs text-gray-500">任务 ID：{taskId.slice(0, 8)}...</p>
                </div>
              </div>
            </div>
            <ProgressView
              taskId={taskId}
              progressPercent={progress.progress_percent}
              currentStage={progress.current_stage}
              stages={progress.stages}
            />
            {err && <div className="max-w-3xl mx-auto mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">{err}</div>}
          </>
        )}

        {stage === 'result' && results && (
          <ResultPanel
            taskId={taskId}
            results={results}
            appInfo={appInfo}
            userGoal={userGoal}
          />
        )}
      </main>

      <footer className="py-8 text-center text-xs text-gray-400">
        © {new Date().getFullYear()} App Review Insight · 离线缓存与降级分析已内置
      </footer>
    </div>
  )
}
