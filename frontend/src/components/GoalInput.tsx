import { useState } from 'react'
import { Target, Sparkles } from 'lucide-react'

interface Props {
  onStart: (goal: string) => void
  loading?: boolean
}

const PRESETS = [
  '全面分析用户反馈，识别核心痛点和高价值改进方向',
  '聚焦稳定性与崩溃问题，找到高优先级 Bug',
  '评估新版本更新效果，关注新版本的正面与负面反馈',
  '分析竞品对比相关的评价，寻找差异化机会',
]

export default function GoalInput({ onStart, loading }: Props) {
  const [goal, setGoal] = useState(PRESETS[0])

  return (
    <div className="w-full max-w-3xl mx-auto mt-6 fade-in">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Target className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold">设定分析目标（可选）</h2>
        </div>
        <textarea
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          placeholder="例如：我想分析这款App的用户反馈，重点关注稳定性、付费转化和新功能体验，优先识别高优先级的问题和机会..."
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
        />
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-2">快速选择目标预设：</p>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p, i) => (
              <button
                key={i}
                onClick={() => setGoal(p)}
                className={`text-xs px-3 py-1.5 rounded-full border transition ${
                  goal === p
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'border-gray-300 text-gray-700 hover:border-primary-500 hover:text-primary-600'
                }`}
              >
                {p.slice(0, 24)}...
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={() => onStart(goal.trim())}
          disabled={loading}
          className="mt-5 w-full py-3.5 bg-gradient-to-r from-primary-600 to-indigo-600 text-white rounded-xl font-medium hover:from-primary-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          {loading ? '启动分析中...' : '开始智能分析'}
        </button>
      </div>
    </div>
  )
}
