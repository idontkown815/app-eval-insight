import { useState } from 'react'
import { Link, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { validateLink } from '../api/client'
import type { AppInfo } from '../types'

interface Props {
  onValid: (bundleId: string, url: string, appInfo: AppInfo) => void
  initialUrl?: string
}

export default function LinkInput({ onValid, initialUrl = '' }: Props) {
  const [url, setUrl] = useState(initialUrl)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null)

  const exampleUrl = 'https://apps.apple.com/us/app/facebook/id284882215'

  const handleValidate = async () => {
    if (!url.trim()) {
      setError('请输入美国 App Store 应用链接')
      return
    }
    setLoading(true)
    setError('')
    setAppInfo(null)
    try {
      const res = await validateLink(url.trim())
      if (!res.valid || !res.app_info || !res.bundle_id) {
        setError(res.error || '链接无效')
      } else {
        setAppInfo(res.app_info)
        onValid(res.bundle_id, url.trim(), res.app_info)
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || '验证失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 fade-in">
        <div className="flex items-center gap-2 mb-4">
          <Link className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold">输入美国 App Store 应用链接</h2>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder={`例如：${exampleUrl}`}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
          />
          <button
            onClick={handleValidate}
            disabled={loading}
            className="px-5 py-3 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {loading ? '验证中...' : '验证链接'}
          </button>
        </div>
        <p className="mt-3 text-xs text-gray-500">
          提示：支持格式 <code>https://apps.apple.com/us/app/应用名称/id数字ID</code>
        </p>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2 fade-in">
            <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {appInfo && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-4 fade-in">
            {appInfo.icon_url && (
              <img src={appInfo.icon_url} alt="icon" className="w-16 h-16 rounded-2xl" />
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{appInfo.name}</h3>
              <p className="text-sm text-gray-600">{appInfo.developer} · {appInfo.category}</p>
              <div className="mt-1 flex items-center gap-3 text-xs text-gray-600">
                <span>评分 {Number(appInfo.rating || 0).toFixed(1)}</span>
                <span>{appInfo.review_count?.toLocaleString?.() || 0} 条评价</span>
                <span>{appInfo.price || '免费'}</span>
              </div>
            </div>
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
        )}
      </div>
    </div>
  )
}
