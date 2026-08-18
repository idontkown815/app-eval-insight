import { ProgressStage } from '../types'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'

interface Props {
  taskId: string
  progressPercent: number
  currentStage: string
  stages: ProgressStage[]
}

const STATUS_STYLE = {
  pending: 'bg-gray-100 text-gray-500',
  in_progress: 'bg-primary-50 text-primary-700 border-primary-200',
  completed: 'bg-green-50 text-green-700 border-green-200',
  failed: 'bg-red-50 text-red-700 border-red-200',
}

export default function ProgressView({ progressPercent, currentStage, stages }: Props) {
  return (
    <div className="w-full max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6 fade-in">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold">分析进度</h2>
        <span className="text-sm font-medium text-primary-600">{progressPercent}%</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2 mb-4 overflow-hidden">
        <div className="step-bar-fill h-full bg-gradient-to-r from-primary-500 to-indigo-500 rounded-full" style={{ width: `${progressPercent}%` }} />
      </div>
      <p className="text-sm text-gray-600 mb-4">当前阶段：<span className="font-medium text-gray-900">{currentStage}</span></p>
      <ul className="space-y-2">
        {stages.map((s, i) => (
          <li key={i} className={`flex items-center gap-3 p-3 rounded-lg border ${STATUS_STYLE[s.status]}`}>
            <div className="w-7 h-7 flex items-center justify-center flex-shrink-0">
              {s.status === 'in_progress' && <Loader2 className="w-5 h-5 animate-spin text-primary-600" />}
              {s.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-600" />}
              {s.status === 'failed' && <XCircle className="w-5 h-5 text-red-600" />}
              {s.status === 'pending' && <span className="w-5 h-5 rounded-full border-2 border-gray-300" />}
            </div>
            <span className="text-sm font-medium">{s.name_cn}</span>
            <span className="ml-auto text-xs opacity-80">{s.status === 'in_progress' ? '执行中...' : s.status === 'completed' ? '完成' : s.status === 'failed' ? '失败' : '待执行'}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
