# App Review Insight · 美国 App Store 评价智能分析平台

## 🎯 项目简介
输入 App Store 链接 → 自动采集、清洗、分类、发现问题 → 输出 PRD / 测试用例 / 追溯链

## ✨ 核心特性
- ✅ 10阶段全流程自动化工作流
- ✅ LLM 驱动的**动态分类**（无硬编码类别）
- ✅ 完整**追溯链**验证：结论→发现→需求→测试用例→原始评价
- ✅ **多源数据采集**：Apple RSS Feed API → Web 爬取 → 本地缓存
- ✅ **离线缓存 + 降级分析**：网络/LLM 不可用时自动切换，缓存数据明确标识
- ✅ CSV / Markdown / JSON 三种格式一键导出
- ✅ 支持 JSON / CSV 文件导入评价数据，适配任意应用
- ✅ 样本数据预置，零配置即可体验

## 🛠️ 技术栈
### 后端
- Python 3.12+ / FastAPI / Uvicorn
- Pydantic / SQLite (stdlib) / Requests
- OpenAI SDK + 自定义 fallback 降级分析器

### 前端
- React 18 / TypeScript 5
- Vite 5 / TailwindCSS 3
- Axios / lucide-react / recharts

## 📁 目录结构
```
app-eval-insight/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── analyzer/        # LLM 分析引擎（7个模块）
│   │   ├── api/             # API 路由
│   │   ├── cache/           # 缓存管理 + 健康检查
│   │   ├── cleaner/         # 数据清洗
│   │   ├── collector/       # 数据采集：链接解析 / RSS / 导入
│   │   ├── generator/       # PRD + 测试用例 + 追溯链
│   │   ├── pipeline/        # 10阶段流程编排
│   │   ├── models/          # 数据库 + Pydantic Schemas
│   │   ├── utils/           # 日志 + 导出器
│   │   ├── config.py        # 配置
│   │   └── main.py          # FastAPI 入口
│   ├── data/                # 数据目录：cache + 样本
│   ├── tests/               # 测试脚本
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/                # React + Vite 前端
│   └── src/
│       ├── components/      # LinkInput / GoalInput / ProgressView / ResultPanel
│       ├── api/client.ts
│       ├── types/index.ts
│       ├── App.tsx
│       └── main.tsx
└── docs/                    # 需求拆解与实现文档
```

## 🚀 快速启动（零配置 Demo 模式）

### 1. 启动后端
```powershell
cd backend
# 创建虚拟环境（首次）
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 启动 FastAPI 服务器
python run.py
# → http://localhost:8000
```

### 2. 启动前端（新开终端）
```powershell
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. 打开浏览器 → http://localhost:5173
**Demo 测试提示**：因为预置了 Facebook(id=284882215) 和 Instagram(id=389801252) 的缓存样本，即使：
- 网络不可用 ✅（从缓存读取评价）
- 没填 LLM API Key ✅（进入关键词+评分降级分析）

你仍能跑完整个流程！

示例输入链接：
```
https://apps.apple.com/us/app/facebook/id284882215
```

## 🧪 冒烟测试（Fallback 降级模式）
```powershell
cd backend
.\.venv\Scripts\python.exe tests\test_fallback_smoke.py
```
预期输出：10 个步骤全部 PASS ✓

## 🔧 配置 LLM（可选，获得智能分析）
复制 `.env.example` 为 `.env` 并填入：
```
LLM_API_KEY=sk-xxxxxx
LLM_BASE_URL=https://api.openai.com/v1   # 兼容代理地址
LLM_MODEL=gpt-4o-mini
```
未配置时自动降级。

## 📡 API 接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/validate-link` | 验证 App Store 链接 |
| POST | `/api/tasks` | 新建分析任务（后台异步） |
| GET | `/api/tasks/{id}/progress` | 获取进度 |
| GET | `/api/tasks/{id}/results` | 获取完整结果 |
| POST | `/api/import` | 上传 JSON/CSV 评价文件 |
| GET | `/api/tasks/{id}/export?format=` | 导出 csv/md/json |
| GET | `/api/health` | 健康检查 |

## 🔄 工作流 10 阶段
1. **确定分析范围** → 目标解析为 focus_areas / intents
2. **数据收集** → App Store RSS / Cache 回退
3. **数据清洗** → 去重 / 剥离HTML / 评分校验 / 日期归一化
4. **动态分类** → LLM 生成类别 or 评分分 3 类
5. **证据评估** → 支撑证据量 + 矛盾发现检测
6. **PRD 生成** → Top 发现 → 需求 / 优先级 / 版本规划
7. **测试用例生成** → Given-When-Then 正反用例
8. **追溯链验证** → 每一条结论都能追到原始评价
9. **结果准备** → 拼装 deliverables
10. **展示** → 前端 Tab 展示并可导出

## 📝 样本数据位置
| 用途 | 路径 |
|------|------|
| Facebook 评价缓存 | `backend/data/cache/reviews/284882215_sample.json` |
| Instagram 评价缓存 | `backend/data/cache/reviews/389801252_sample.json` |
| 实时采集缓存 | `backend/data/cache/reviews/{bundle_id}_{timestamp}.json` |
| CSV 导入测试 | `backend/data/sample_reviews.csv` |
| JSON 导入测试 | `backend/data/sample_reviews.json` |
| 样本分析结果 | `backend/data/sample_output.json` |

> **缓存数据说明**：所有缓存文件均为真实从 App Store 采集的数据，非伪造。
> 文件名中带 `_sample` 后缀的为预置样本（用于离线演示），带时间戳的为实时采集缓存。
> 系统始终优先尝试实时采集，仅在网络不可用时回退到缓存。缓存数据不会取代实时处理能力——
> 当网络和模型配置可用时，系统会对任意未见过的 App Store 应用链接实时采集并分析。
> 结果中通过 `data_source` 和 `data_fetch_note` 字段透明标识数据来源。

## 📡 数据采集方法说明

### 采集策略（多源降级）
1. **Apple RSS Feed API**（首选）：`itunes.apple.com/us/rss/customerreviews/id={id}/json`
   - Apple 官方公开的评价数据接口，数据真实可重复
   - 局限性：近年来 Apple 逐步收紧该接口，对大量主流应用返回空数据
2. **App Store Web 数据**（备选）：解析 `viewSoftware` 页面嵌入的 JSON
   - 当 RSS 不可用时，通过 HTTP 请求获取 App Store 页面，解析其中嵌入的评论 JSON
   - 局限性：页面通常只包含精选评价（最多约 40 条），不代表全部用户评价
3. **本地缓存**（降级）：使用上次采集的真实数据
   - 当网络不可用时自动回退，结果中标记 `data_source: "cache"`
   - 缓存有效期默认 7 天（可配置 `CACHE_VALIDITY_DAYS`）
4. **文件导入**（补充）：支持 JSON / CSV 格式导入第三方数据

### 不依赖特定应用硬编码
系统不绑定任何特定应用的 ID 或配置。任何美国 App Store 应用链接均可输入并分析。
健康检查使用 Apple Search API 通用查询，不依赖特定应用。

## 📥 JSON / CSV 导入格式

### JSON 格式
```json
{
  "reviews": [
    {
      "review_id": "unique_id_1",
      "author": "用户名",
      "rating": 5,
      "title": "评价标题",
      "content": "评价正文内容",
      "review_date": "2026-08-15T08:30:00Z",
      "version": "应用版本号（可选）"
    }
  ]
}
```

### CSV 格式
```csv
review_id,author,rating,title,content,review_date,version
r001,User1,5,"Great app","This is a great app!","2026-08-15T08:30:00Z",453
r002,User2,1,"Crashes","App keeps crashing on startup","2026-08-14T10:00:00Z",453
```

**必填字段**：`review_id`、`rating`（1-5 整数）、`content`（非空文本）、`review_date`

导入后系统自动执行完整分析流程（清洗 → 分类 → 发现 → PRD → 测试用例 → 追溯链）。

## 📜 License
MIT

---

# App Review Insight · US App Store Review Intelligent Analysis Platform

## 🎯 Project Introduction
Input App Store link → auto collect, clean, classify, identify issues → output PRD / Test Cases / Traceability Chain

## ✨ Core Features
- ✅ 10-stage fully automated workflow
- ✅ LLM-powered **dynamic classification** (no hardcoded categories)
- ✅ Complete **traceability chain** verification: conclusion → findings → requirements → test cases → original reviews
- ✅ **Multi-source data collection**: Apple RSS Feed API → Web scraping → Local cache
- ✅ **Offline cache + fallback analysis**: auto switch when network/LLM unavailable, cache data clearly marked
- ✅ One-click export in CSV / Markdown / JSON formats
- ✅ Supports JSON / CSV file import for review data, works with any app
- ✅ Preloaded sample data, zero-config ready to experience

## 🛠️ Tech Stack
### Backend
- Python 3.12+ / FastAPI / Uvicorn
- Pydantic / SQLite (stdlib) / Requests
- OpenAI SDK + Custom fallback analyzer

### Frontend
- React 18 / TypeScript 5
- Vite 5 / TailwindCSS 3
- Axios / lucide-react / recharts

## 📁 Directory Structure
```
app-eval-insight/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── analyzer/        # LLM Analysis Engine (7 modules)
│   │   ├── api/             # API Routes
│   │   ├── cache/           # Cache Management + Health Check
│   │   ├── cleaner/         # Data Cleaning
│   │   ├── collector/       # Data Collection: Link Parse / RSS / Import
│   │   ├── generator/       # PRD + Test Cases + Traceability
│   │   ├── pipeline/        # 10-stage Pipeline Orchestration
│   │   ├── models/          # Database + Pydantic Schemas
│   │   ├── utils/           # Logger + Exporter
│   │   ├── config.py        # Configuration
│   │   └── main.py          # FastAPI Entry Point
│   ├── data/                # Data Dir: cache + samples
│   ├── tests/               # Test Scripts
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/                # React + Vite Frontend
│   └── src/
│       ├── components/      # LinkInput / GoalInput / ProgressView / ResultPanel
│       ├── api/client.ts
│       ├── types/index.ts
│       ├── App.tsx
│       └── main.tsx
└── docs/                    # Requirements & Implementation Docs
```

## 🚀 Quick Start (Zero-Config Demo Mode)

### 1. Start Backend
```powershell
cd backend
# Create venv (first time)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start FastAPI Server
python run.py
# → http://localhost:8000
```

### 2. Start Frontend (New Terminal)
```powershell
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Open Browser → http://localhost:5173
**Demo Testing Hint**: Preloaded cache samples for Facebook(id=284882215) and Instagram(id=389801252), even when:
- Network unavailable ✅ (read reviews from cache)
- No LLM API Key ✅ (enter keyword + rating fallback analysis)

You can still run the entire pipeline!

Sample input link:
```
https://apps.apple.com/us/app/facebook/id284882215
```

## 🧪 Smoke Test (Fallback Mode)
```powershell
cd backend
.\.venv\Scripts\python.exe tests\test_fallback_smoke.py
```
Expected output: All 10 steps PASS ✓

## 🔧 Configure LLM (Optional, for Intelligent Analysis)
Copy `.env.example` to `.env` and fill in:
```
LLM_API_KEY=sk-xxxxxx
LLM_BASE_URL=https://api.openai.com/v1   # Compatible proxy URL
LLM_MODEL=gpt-4o-mini
```
Auto fallback when not configured.

## 📡 API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/validate-link` | Validate App Store link |
| POST | `/api/tasks` | Create analysis task (async background) |
| GET | `/api/tasks/{id}/progress` | Get progress |
| GET | `/api/tasks/{id}/results` | Get complete results |
| POST | `/api/import` | Upload JSON/CSV review file |
| GET | `/api/tasks/{id}/export?format=` | Export csv/md/json |
| GET | `/api/health` | Health check |

## 🔄 Workflow 10 Stages
1. **Define Analysis Scope** → Goals parsed into focus_areas / intents
2. **Data Collection** → App Store RSS / Cache fallback
3. **Data Cleaning** → Deduplicate / strip HTML / rating validation / date normalization
4. **Dynamic Classification** → LLM generates categories or rating-based 3 categories
5. **Evidence Evaluation** → Supporting evidence count + contradiction detection
6. **PRD Generation** → Top findings → Requirements / Priority / Version planning
7. **Test Case Generation** → Given-When-Then positive/negative cases
8. **Traceability Chain Verification** → Every conclusion traces to original reviews
9. **Result Preparation** → Assemble deliverables
10. **Presentation** → Frontend Tab display with export options

## 📝 Sample Data Locations
| Purpose | Path |
|---------|------|
| Facebook review cache | `backend/data/cache/reviews/284882215_sample.json` |
| Instagram review cache | `backend/data/cache/reviews/389801252_sample.json` |
| Live-collected cache | `backend/data/cache/reviews/{bundle_id}_{timestamp}.json` |
| CSV import test | `backend/data/sample_reviews.csv` |
| JSON import test | `backend/data/sample_reviews.json` |
| Sample analysis output | `backend/data/sample_output.json` |

> **Cache Data Note**: All cache files contain real data collected from App Store, not fabricated.
> Files with `_sample` suffix are preloaded samples (for offline demo). Files with timestamps are live-collected caches.
> The system always attempts live collection first, falling back to cache only when network is unavailable.
> Cache does NOT replace live processing — when network and model config are available, the system processes
> any unseen App Store app link in real time. Data source is transparently indicated via `data_source` and
> `data_fetch_note` fields in results.

## 📡 Data Collection Methods

### Collection Strategy (Multi-source Fallback)
1. **Apple RSS Feed API** (primary): `itunes.apple.com/us/rss/customerreviews/id={id}/json`
   - Apple's official public review data interface, real and reproducible
   - Limitation: Apple has gradually restricted this API, returning empty for many popular apps
2. **App Store Web Data** (fallback): Parse embedded JSON from `viewSoftware` page
   - When RSS unavailable, fetches App Store page via HTTP and parses embedded review JSON
   - Limitation: Page typically contains only featured reviews (max ~40), not all user reviews
3. **Local Cache** (degraded): Use previously collected real data
   - Auto-fallback when network unavailable, marked with `data_source: "cache"` in results
   - Cache validity default 7 days (configurable via `CACHE_VALIDITY_DAYS`)
4. **File Import** (supplement): Support JSON / CSV format for third-party data

### No Hardcoded App Dependencies
The system does not bind to any specific app ID or configuration. Any US App Store app link can be input and analyzed.
Health check uses Apple Search API generic query, not tied to any specific app.

## 📥 JSON / CSV Import Format

### JSON Format
```json
{
  "reviews": [
    {
      "review_id": "unique_id_1",
      "author": "username",
      "rating": 5,
      "title": "Review title",
      "content": "Review body text",
      "review_date": "2026-08-15T08:30:00Z",
      "version": "app version (optional)"
    }
  ]
}
```

### CSV Format
```csv
review_id,author,rating,title,content,review_date,version
r001,User1,5,"Great app","This is a great app!","2026-08-15T08:30:00Z",453
r002,User2,1,"Crashes","App keeps crashing on startup","2026-08-14T10:00:00Z",453
```

**Required fields**: `review_id`, `rating` (integer 1-5), `content` (non-empty text), `review_date`

After import, the system runs the full analysis pipeline (clean → classify → findings → PRD → test cases → traceability).

## 📜 License
MIT
