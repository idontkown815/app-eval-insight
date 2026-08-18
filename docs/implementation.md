# App Review Insight - 开发实现文档

> 本文档是面向 AI 开发代理（Trae Code Agent）的工程实现指南，基于 [requirements.md](file:///d:/app-eval-insight/docs/requirements.md) 编写。
> 文档包含：项目结构、技术栈配置、模块实现细节、全流程实现顺序与验证方案。

---

## 目录

- [1. 技术架构总览](#1-技术架构总览)
- [2. 项目目录结构](#2-项目目录结构)
- [3. 技术栈与依赖配置](#3-技术栈与依赖配置)
- [4. 后端实现方案](#4-后端实现方案)
  - [4.1 数据采集层](#41-数据采集层)
  - [4.2 数据清洗层](#42-数据清洗层)
  - [4.3 LLM 分析引擎](#43-llm-分析引擎)
  - [4.4 文档生成层](#44-文档生成层)
  - [4.5 缓存与离线模块](#45-缓存与离线模块)
  - [4.6 API 路由层](#46-api-路由层)
- [5. 前端实现方案](#5-前端实现方案)
  - [5.1 页面结构与路由](#51-页面结构与路由)
  - [5.2 核心组件实现](#52-核心组件实现)
  - [5.3 状态管理](#53-状态管理)
  - [5.4 API 对接层](#54-api-对接层)
- [6. 数据库设计与初始化](#6-数据库设计与初始化)
- [7. 全流程实现顺序](#7-全流程实现顺序)
- [8. 端到端验证方案](#8-端到端验证方案)
- [9. 部署与运行](#9-部署与运行)

---

## 1. 技术架构总览

### 1.1 整体架构

```
┌──────────────────────────────────────────────────────────┐
│                    前端 (React + Vite)                     │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │链接输入  │ │目标配置   │ │进度追踪   │ │结果展示/导出  │ │
│  │组件      │ │组件      │ │组件      │ │组件          │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP API (JSON)
└────────────────────────┴─────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│                  后端 (Python FastAPI)                     │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ API 路由层   │→│ 业务编排层   │→│  数据采集层       │  │
│  │             │  │ (Pipeline)  │  │  - RSS爬虫        │  │
│  │ /validate   │  │             │  │  - 链接解析       │  │
│  │ /tasks      │  │ 10个阶段    │  │  - 数据导入       │  │
│  │ /progress   │  │ 状态机      │  └──────────────────┘  │
│  │ /results    │  │             │  ┌──────────────────┐  │
│  │ /import     │  │             │→│  LLM 分析引擎     │  │
│  │ /export     │  │             │  │  - 目标理解       │  │
│  └─────────────┘  └─────────────┘  │  - 动态分类       │  │
│                                     │  - 发现生成       │  │
│                                     │  - 追溯链验证     │  │
│                                     └──────────────────┘  │
│                                     ┌──────────────────┐  │
│                                     │  文档生成层       │  │
│                                     │  - PRD 生成       │  │
│                                     │  - 测试用例生成   │  │
│                                     │  - 导出服务       │  │
│                                     └──────────────────┘  │
└────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                    数据存储层                              │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │ SQLite   │  │ JSON 缓存  │  │ 导出文件目录          │  │
│  │ (结构化)  │  │ (评价数据) │  │ (markdown/csv/json)  │  │
│  └──────────┘  └────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 1.2 核心数据流

```
用户输入链接
    │
    ▼
[1] 链接解析 → 提取 bundle_id → 获取应用元数据
    │
    ▼
[2] 数据采集 → RSS Feed API / 缓存 / 文件导入
    │
    ▼
[3] 数据清洗 → 去重、格式化、标准化
    │
    ▼
[4] 目标理解 → LLM 解析用户自由文本目标 → 提取关注点
    │
    ▼
[5] 动态分类 → LLM 按批次分类评价 → 聚类主题
    │
    ▼
[6] 证据评估 → 检查支撑数量、矛盾检测、数据限制标记
    │
    ▼
[7] 发现生成 → LLM 生成 Top N 发现 + 关联评价 ID
    │
    ▼
[8] PRD 生成 → LLM 生成需求条目 + 版本拆分
    │
    ▼
[9] 测试用例 → LLM 生成 Given/When/Then 用例 + 关联需求
    │
    ▼
[10] 追溯链验证 → LLM/规则 验证 评价→发现→需求→用例 链路
    │
    ▼
结果展示 → 前端渲染所有交付物
```

---

## 2. 项目目录结构

```
app-eval-insight/
├── docs/                          # 文档
│   ├── requirements.md            # 需求文档
│   └── implementation.md          # 本实现文档
│
├── backend/                       # Python 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 应用入口
│   │   ├── config.py              # 配置管理（环境变量）
│   │   │
│   │   ├── api/                   # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── routes.py          # 路由注册
│   │   │   ├── validate.py        # 链接验证接口
│   │   │   ├── tasks.py           # 分析任务接口
│   │   │   ├── import_data.py     # 数据导入接口
│   │   │   └── export.py          # 导出接口
│   │   │
│   │   ├── collector/             # 数据采集层
│   │   │   ├── __init__.py
│   │   │   ├── app_store.py       # App Store RSS 爬虫
│   │   │   ├── link_parser.py     # 链接解析器
│   │   │   └── file_importer.py   # JSON/CSV 文件导入
│   │   │
│   │   ├── cleaner/              # 数据清洗层
│   │   │   ├── __init__.py
│   │   │   └── review_cleaner.py  # 评价数据清洗
│   │   │
│   │   ├── analyzer/              # LLM 分析引擎
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py     # LLM API 调用封装
│   │   │   ├── goal_understander.py  # 目标理解模块
│   │   │   ├── classifier.py     # 动态分类引擎
│   │   │   ├── finding_generator.py  # 发现生成引擎
│   │   │   ├── evidence_evaluator.py # 证据评估模块
│   │   │   └── fallback_analyzer.py # 无LLM降级分析
│   │   │
│   │   ├── generator/            # 文档生成层
│   │   │   ├── __init__.py
│   │   │   ├── prd_generator.py  # PRD 生成器
│   │   │   ├── test_case_generator.py  # 测试用例生成器
│   │   │   └── traceability_checker.py  # 追溯链验证器
│   │   │
│   │   ├── cache/                # 缓存模块
│   │   │   ├── __init__.py
│   │   │   ├── cache_manager.py  # 缓存读写管理
│   │   │   └── health_checker.py # 网络/LLM 可用性检测
│   │   │
│   │   ├── pipeline/             # 流程编排层
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # 10阶段流程编排器
│   │   │   └── stage_tracker.py  # 阶段状态追踪器
│   │   │
│   │   ├── models/               # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── database.py       # SQLite 连接与表定义
│   │   │   └── schemas.py        # Pydantic 数据模型
│   │   │
│   │   └── utils/                # 工具函数
│   │       ├── __init__.py
│   │       ├── exporter.py       # 导出工具
│   │       └── logger.py         # 日志配置
│   │
│   ├── data/                     # 数据目录
│   │   ├── cache/                # 缓存文件
│   │   │   ├── cache_index.json  # 缓存索引
│   │   │   ├── reviews/          # 评价缓存
│   │   │   └── analysis/         # 分析结果缓存
│   │   ├── db/                   # SQLite 数据库
│   │   │   └── app_review.db
│   │   ├── exports/              # 导出文件
│   │   └── samples/              # 样本数据
│   │       └── sample_reviews.json
│   │
│   ├── requirements.txt          # Python 依赖
│   ├── .env.example              # 环境变量示例
│   └── run.py                    # 启动脚本
│
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── main.tsx              # 应用入口
│   │   ├── App.tsx               # 根组件
│   │   │
│   │   ├── components/           # UI 组件
│   │   │   ├── LinkInput.tsx     # 链接输入组件
│   │   │   ├── AppPreview.tsx    # 应用预览卡片
│   │   │   ├── GoalInput.tsx     # 分析目标输入
│   │   │   ├── FilterConfig.tsx  # 筛选条件配置
│   │   │   ├── ProgressTracker.tsx  # 进度追踪面板
│   │   │   ├── ResultsView.tsx   # 结果展示
│   │   │   ├── ReviewTable.tsx  # 评价数据表格
│   │   │   ├── CategoryChart.tsx # 分类可视化
│   │   │   ├── FindingCards.tsx  # 发现卡片
│   │   │   ├── PRDViewer.tsx     # PRD 预览
│   │   │   ├── TestCaseTable.tsx # 测试用例表格
│   │   │   ├── TraceabilityView.tsx  # 追溯链展示
│   │   │   ├── CacheBanner.tsx   # 缓存标识横幅
│   │   │   ├── DataImport.tsx    # 数据导入组件
│   │   │   └── ExportButton.tsx  # 导出按钮
│   │   │
│   │   ├── pages/               # 页面
│   │   │   └── HomePage.tsx     # 主页（单页应用）
│   │   │
│   │   ├── hooks/               # 自定义 Hooks
│   │   │   ├── useAnalysisTask.ts  # 分析任务管理
│   │   │   └── useProgressPoll.ts # 进度轮询
│   │   │
│   │   ├── services/            # API 对接层
│   │   │   └── api.ts            # 后端 API 调用封装
│   │   │
│   │   ├── types/               # TypeScript 类型
│   │   │   └── index.ts         # 全局类型定义
│   │   │
│   │   └── utils/               # 工具函数
│   │       └── format.ts        # 格式化工具
│   │
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docker-compose.yml            # Docker 编排
└── README.md                     # 项目说明
```

---

## 3. 技术栈与依赖配置

### 3.1 后端依赖 (requirements.txt)

```txt
# Web 框架
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.5.0

# 数据采集
requests==2.31.0
beautifulsoup4==4.12.0

# LLM 集成
openai==1.12.0          # 兼容 OpenAI 格式的多模型调用

# 数据处理
python-dateutil==2.8.2

# 文件处理
python-multipart==0.0.6  # 文件上传

# 导出
markdown==3.5.1          # Markdown 渲染
```

### 3.2 前端依赖 (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "recharts": "^2.12.0",
    "lucide-react": "^0.358.0",
    "react-markdown": "^9.0.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0"
  }
}
```

### 3.3 环境变量配置 (.env)

```bash
# === LLM 配置 ===
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# === App Store 配置 ===
APP_STORE_REGION=us
REQUEST_DELAY_SECONDS=1

# === 服务配置 ===
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173

# === 缓存配置 ===
CACHE_VALIDITY_DAYS=7
CACHE_DIR=./data/cache
```

---

## 4. 后端实现方案

### 4.1 数据采集层

#### 4.1.1 链接解析器 (link_parser.py)

**职责**：解析 App Store 链接，提取 bundle_id，获取应用元数据。

```python
# 实现要点：
# 1. 正则匹配 https://apps.apple.com/us/app/.+/id\d+
# 2. 提取 bundle_id（id 后面的数字）
# 3. 调用 iTunes Lookup API 获取应用信息
# 4. 返回应用名称、开发者、图标、价格等

import re
import requests

class LinkParser:
    URL_PATTERN = r'https://apps\.apple\.com/us/app/[^/]+/id(\d+)'
    LOOKUP_URL = "https://itunes.apple.com/lookup?id={bundle_id}"

    def parse(self, url: str) -> dict:
        """解析链接，返回 bundle_id"""
        match = re.match(self.URL_PATTERN, url)
        if not match:
            raise ValueError("无效的 App Store US 链接")
        bundle_id = match.group(1)
        return {"bundle_id": bundle_id, "valid": True}

    def fetch_app_info(self, bundle_id: str) -> dict:
        """调用 iTunes Lookup API 获取应用信息"""
        url = self.LOOKUP_URL.format(bundle_id=bundle_id)
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["resultCount"] == 0:
            raise ValueError("应用不存在")
        result = data["results"][0]
        return {
            "name": result.get("trackName"),
            "developer": result.get("artistName"),
            "price": result.get("price", 0),
            "category": result.get("primaryGenreName"),
            "icon_url": result.get("artworkUrl100"),
            "rating": result.get("averageUserRating"),
            "review_count": result.get("userRatingCount"),
        }
```

#### 4.1.2 App Store RSS 爬虫 (app_store.py)

**职责**：通过 RSS Feed API 分页采集评价数据。

```python
# 实现要点：
# 1. 调用 https://itunes.apple.com/us/rss/customerreviews/id={bundle_id}/sortBy=mostRecent/json
# 2. 分页获取（page=1,2,... 直到无数据）
# 3. 每次请求间隔 ≥ 1 秒
# 4. 每页返回最多 50 条，最多获取 500 条
# 5. 返回标准化的评价列表

class AppStoreCrawler:
    RSS_URL = "https://itunes.apple.com/us/rss/customerreviews/id={bundle_id}/sortBy=mostRecent/page={page}/json"

    def fetch_reviews(self, bundle_id: str, max_pages: int = 10) -> list:
        """采集评价数据"""
        all_reviews = []
        for page in range(1, max_pages + 1):
            url = self.RSS_URL.format(bundle_id=bundle_id, page=page)
            resp = requests.get(url, timeout=15)
            data = resp.json()
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
            for entry in entries:
                review = self._parse_entry(entry)
                if review:
                    all_reviews.append(review)
            time.sleep(1)  # 请求间隔
        return all_reviews

    def _parse_entry(self, entry: dict) -> dict | None:
        """解析单条评价"""
        # RSS 返回的字段名可能带有前缀，需要提取
        try:
            return {
                "review_id": entry["id"]["label"],
                "author": entry["author"]["name"]["label"],
                "rating": int(entry["im:rating"]["label"]),
                "title": entry["title"]["label"],
                "content": entry["content"]["label"],
                "review_date": entry["updated"]["label"],
                "version": entry.get("im:version", {}).get("label", ""),
            }
        except (KeyError, ValueError):
            return None
```

#### 4.1.3 文件导入器 (file_importer.py)

**职责**：解析用户上传的 JSON/CSV 文件。

```python
# 实现要点：
# 1. JSON 格式：解析 {"app_name": "...", "reviews": [...]} 结构
# 2. CSV 格式：用 csv.DictReader 解析
# 3. 验证必填字段：review_id, rating, content, review_date
# 4. 返回 (valid_reviews, invalid_count, statistics)

class FileImporter:
    REQUIRED_FIELDS = ["review_id", "rating", "content", "review_date"]

    def import_json(self, file_content: bytes) -> dict:
        """导入 JSON 文件"""
        data = json.loads(file_content)
        reviews = data.get("reviews", [])
        return self._validate_reviews(reviews)

    def import_csv(self, file_content: bytes) -> dict:
        """导入 CSV 文件"""
        text = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        reviews = list(reader)
        return self._validate_reviews(reviews)

    def _validate_reviews(self, reviews: list) -> dict:
        """验证评价数据，返回有效/无效统计"""
        valid, invalid = [], 0
        for r in reviews:
            if all(f in r and r[f] for f in self.REQUIRED_FIELDS):
                valid.append(r)
            else:
                invalid += 1
        return {"valid_reviews": valid, "invalid_count": invalid}
```

### 4.2 数据清洗层

#### review_cleaner.py

**职责**：去重、格式化、标准化评价数据。

```python
# 实现要点：
# 1. 按 review_id 去重
# 2. 移除空内容评价
# 3. 修正 rating 字段为 int(1-5)
# 4. 标准化日期格式为 YYYY-MM-DD
# 5. 去除 HTML 标签
# 6. 返回清洗后的评价列表 + 清洁度报告

class ReviewCleaner:
    def clean(self, raw_reviews: list) -> dict:
        """清洗评价数据"""
        # 去重
        seen_ids = set()
        deduped = []
        for r in raw_reviews:
            rid = r.get("review_id")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                deduped.append(r)

        # 过滤和标准化
        cleaned = []
        for r in deduped:
            content = self._strip_html(r.get("content", ""))
            if not content.strip():
                continue  # 移除空内容
            rating = int(r["rating"])
            if rating < 1 or rating > 5:
                continue
            date = self._normalize_date(r["review_date"])
            cleaned.append({
                "review_id": r["review_id"],
                "author": r.get("author", "Anonymous"),
                "rating": rating,
                "title": r.get("title", ""),
                "content": content,
                "review_date": date,
                "version": r.get("version", ""),
            })

        return {
            "cleaned_reviews": cleaned,
            "original_count": len(raw_reviews),
            "cleaned_count": len(cleaned),
            "removed_count": len(raw_reviews) - len(cleaned),
        }

    def _strip_html(self, text: str) -> str:
        """去除 HTML 标签"""
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

    def _normalize_date(self, date_str: str) -> str:
        """标准化日期为 YYYY-MM-DD"""
        from dateutil import parser
        try:
            dt = parser.parse(date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return date_str
```

### 4.3 LLM 分析引擎

#### 4.3.1 LLM 客户端封装 (llm_client.py)

**职责**：封装 LLM API 调用，支持超时、重试、降级。

```python
# 实现要点：
# 1. 使用 openai SDK（兼容 OpenAI 格式的多模型）
# 2. 支持环境变量配置 API Key / Base URL / Model
# 3. 单次调用超时 30 秒，最多重试 2 次
# 4. 返回 JSON 解析结果（LLM 输出需为 JSON）
# 5. 失败时抛出可被编排器捕获的异常

import os
import json
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.available = bool(self.api_key)

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        """调用 LLM，要求返回 JSON"""
        if not self.available:
            raise RuntimeError("LLM 未配置")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=30,
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self.available
```

#### 4.3.2 目标理解模块 (goal_understander.py)

**职责**：解析用户自由文本目标，提取关注点。

```python
# 实现要点：
# 1. 使用 requirements.md 中定义的 GOAL_UNDERSTANDING_PROMPT
# 2. 输入：用户自由文本目标
# 3. 输出：focus_areas[], analysis_intents[], suggested_filters
# 4. 若用户目标为空，返回默认全面分析

SYSTEM_PROMPT = "你是一个应用评审分析专家，请分析用户的分析目标。"

USER_PROMPT_TEMPLATE = """
请分析以下用户的分析目标，提取关键关注点和分析维度。

用户目标：{user_goal}

请输出 JSON：
{{
  "focus_areas": ["关注点1", "关注点2", ...],
  "analysis_intents": ["意图1", "意图2", ...],
  "suggested_filters": {{"rating": [], "time_range": ""}}
}}
"""

class GoalUnderstander:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def understand(self, user_goal: str) -> dict:
        """理解用户分析目标"""
        if not user_goal or not user_goal.strip():
            return self._default_goal()
        prompt = USER_PROMPT_TEMPLATE.format(user_goal=user_goal)
        result = self.llm.chat_json(SYSTEM_PROMPT, prompt)
        return result

    def _default_goal(self) -> dict:
        """默认全面分析目标"""
        return {
            "focus_areas": ["全面分析"],
            "analysis_intents": ["识别问题", "评估满意度", "发现改进机会"],
            "suggested_filters": {},
        }
```

#### 4.3.3 动态分类引擎 (classifier.py)

**职责**：LLM 动态分类评价（核心模块，不使用预设类别）。

```python
# 实现要点：
# 1. 使用 requirements.md 中的 DYNAMIC_CLASSIFICATION_PROMPT
# 2. 将评价分批（每批 30-50 条）发送给 LLM
# 3. LLM 返回动态生成的类别名 + 类别下的 review_ids
# 4. 合并多批结果，对相似类别做二次聚类
# 5. 每个类别记录：name, description, review_ids, sentiment, key_points

CLASSIFY_SYSTEM = "你是一个应用评审分析专家，请对评价进行动态分类。"

CLASSIFY_USER_TEMPLATE = """
分析关注点：{focus_areas}

评价数据（共 {batch_size} 条）：
{reviews_batch}

请对评价进行动态分类，类别名应具体反映内容。
输出 JSON：{{"categories": [{{"name": "...", "description": "...", "review_ids": [...], "sentiment": "...", "key_points": [...]}}]}}
"""

class DynamicClassifier:
    BATCH_SIZE = 30  # 每批发送的评价数

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def classify(self, reviews: list, focus_areas: list) -> list:
        """动态分类所有评价"""
        # 分批处理
        batches = [reviews[i:i+self.BATCH_SIZE]
                   for i in range(0, len(reviews), self.BATCH_SIZE)]

        all_categories = []
        for batch in batches:
            reviews_text = self._format_reviews(batch)
            prompt = CLASSIFY_USER_TEMPLATE.format(
                focus_areas=focus_areas,
                batch_size=len(batch),
                reviews_batch=reviews_text,
            )
            result = self.llm.chat_json(CLASSIFY_SYSTEM, prompt)
            all_categories.extend(result.get("categories", []))

        # 合并相似类别
        merged = self._merge_similar(all_categories)
        return merged

    def _format_reviews(self, reviews: list) -> str:
        """格式化评价为 LLM 输入文本"""
        lines = []
        for r in reviews:
            lines.append(f'[ID:{r["review_id"]}] 评分:{r["rating"]}星 内容:{r["content"]}')
        return "\n".join(lines)

    def _merge_similar(self, categories: list) -> list:
        """合并名称相似的类别"""
        # 简单实现：相同名称合并，不同名称保留
        merged = {}
        for cat in categories:
            name = cat["name"]
            if name in merged:
                merged[name]["review_ids"].extend(cat.get("review_ids", []))
            else:
                merged[name] = cat
        return list(merged.values())
```

#### 4.3.4 发现生成引擎 (finding_generator.py)

**职责**：基于分类结果生成关键发现。

```python
# 实现要点：
# 1. 使用 requirements.md 中的 FINDING_GENERATION_PROMPT
# 2. 输入：分类结果 + 用户目标
# 3. 输出：Top 5 发现，每个发现含 title, description, evidence_strength,
#    supporting_review_ids, representative_quotes, suggested_action
# 4. 证据强度规则：>20条=strong, 10-20=medium, <10=weak

FINDING_SYSTEM = "你是一个应用评审分析专家，请基于分类结果生成关键发现。"

FINDING_USER_TEMPLATE = """
分析目标：{user_goal}
分类结果：{classification_results}

请生成 Top 5 关键发现。
输出 JSON：{{"findings": [{{"title": "...", "description": "...", "evidence_strength": "strong/medium/weak", "supporting_review_ids": [], "representative_quotes": [], "suggested_action": "...", "is_positive": true/false}}]}}
"""

class FindingGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, categories: list, reviews: list, user_goal: str) -> list:
        """生成关键发现"""
        # 准备分类结果摘要
        cat_summary = json.dumps([
            {"name": c["name"], "count": len(c.get("review_ids", [])),
             "sentiment": c.get("sentiment")}
            for c in categories
        ], ensure_ascii=False)

        prompt = FINDING_USER_TEMPLATE.format(
            user_goal=user_goal,
            classification_results=cat_summary,
        )
        result = self.llm.chat_json(FINDING_SYSTEM, prompt)
        return result.get("findings", [])
```

#### 4.3.5 证据评估模块 (evidence_evaluator.py)

**职责**：评估发现的证据充分性，检测矛盾反馈。

```python
# 实现要点：
# 1. 检查每个发现的 supporting_review_ids 数量
# 2. 标记证据强度（规则计算，非 LLM）
# 3. 检测矛盾：同一主题内有正面和负面评价
# 4. 标记数据限制（样本不足、时间窗口）

class EvidenceEvaluator:
    MIN_EVIDENCE = 3  # 最少支撑评价数

    def evaluate(self, findings: list, reviews: list) -> list:
        """评估发现的证据充分性"""
        review_map = {r["review_id"]: r for r in reviews}

        for finding in findings:
            ids = finding.get("supporting_review_ids", [])
            count = len(ids)

            # 证据强度
            if count > 20:
                finding["evidence_strength"] = "strong"
            elif count >= 10:
                finding["evidence_strength"] = "medium"
            else:
                finding["evidence_strength"] = "weak"

            # 检测矛盾
            ratings = [review_map[rid]["rating"]
                       for rid in ids if rid in review_map]
            if ratings:
                avg = sum(ratings) / len(ratings)
                has_high = any(r >= 4 for r in ratings)
                has_low = any(r <= 2 for r in ratings)
                finding["is_contradictory"] = has_high and has_low
            else:
                finding["is_contradictory"] = False

            # 数据限制标记
            if count < self.MIN_EVIDENCE:
                finding["data_limitation"] = "支撑评价不足（少于3条）"

        return findings
```

#### 4.3.6 降级分析器 (fallback_analyzer.py)

**职责**：LLM 不可用时的基础统计分析。

```python
# 实现要点：
# 1. 关键词频率统计生成伪分类
# 2. 情感词典匹配判断正负面
# 3. 高频问题统计生成伪发现
# 4. 结果标记为"基础分析（无LLM）"

class FallbackAnalyzer:
    # 简单情感词典
    POSITIVE_WORDS = ["good", "great", "love", "excellent", "perfect", "amazing", "best"]
    NEGATIVE_WORDS = ["bad", "terrible", "hate", "crash", "bug", "slow", "worst", "broken"]

    def analyze(self, reviews: list, user_goal: str) -> dict:
        """无LLM降级分析"""
        # 1. 基于关键词频率的简单分类
        categories = self._keyword_categorize(reviews)

        # 2. 简单情感分析
        for cat in categories:
            cat["sentiment"] = self._sentiment_for_category(cat, reviews)

        # 3. 生成基础发现
        findings = self._basic_findings(categories, reviews)

        return {
            "categories": categories,
            "findings": findings,
            "is_fallback": True,
            "warning": "当前为基础统计分析模式（LLM不可用），结果质量有限",
        }

    def _keyword_categorize(self, reviews):
        """基于关键词频率分类"""
        # 统计高频词，取 Top 8 作为类别
        # ... 实现略
        pass

    def _sentiment_for_category(self, category, reviews):
        """情感词典匹配"""
        # ... 实现略
        pass
```

### 4.4 文档生成层

#### 4.4.1 PRD 生成器 (prd_generator.py)

**职责**：基于发现生成结构化 PRD。

```python
# 实现要点：
# 1. 使用 LLM 将发现转化为需求条目
# 2. 每个需求关联到 finding_id
# 3. 若发现 > 15 条，建议拆分版本（V1 核心 / V2 增强）
# 4. 生成 Markdown 格式 PRD

PRD_SYSTEM = "你是产品经理，请基于分析发现生成结构化的PRD文档。"

PRD_USER_TEMPLATE = """
分析目标：{user_goal}
发现列表：{findings}

请将发现转化为产品需求，生成PRD。
输出 JSON：
{{
  "requirements": [
    {{
      "id": "REQ-001",
      "finding_id": "关联的发现ID",
      "title": "需求标题",
      "user_story": "作为...，我想要...，以便...",
      "priority": "P0/P1/P2",
      "version_suggestion": "V1/V2"
    }}
  ],
  "version_plan": {{
    "V1": "核心需求范围说明",
    "V2": "增强需求范围说明"
  }}
}}
"""

class PRDGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, findings: list, user_goal: str) -> dict:
        """生成 PRD"""
        findings_summary = json.dumps([
            {"id": f.get("id", i), "title": f["title"],
             "description": f.get("description", ""),
             "strength": f.get("evidence_strength", "medium")}
            for i, f in enumerate(findings)
        ], ensure_ascii=False)

        prompt = PRD_USER_TEMPLATE.format(
            user_goal=user_goal,
            findings=findings_summary,
        )
        result = self.llm.chat_json(PRD_SYSTEM, prompt)
        return result

    def to_markdown(self, prd_data: dict, app_info: dict) -> str:
        """将 PRD 转为 Markdown 文本"""
        # 生成完整 PRD Markdown
        # 包含：概述、用户故事列表、版本规划
        # ... 实现略
        pass
```

#### 4.4.2 测试用例生成器 (test_case_generator.py)

**职责**：基于 PRD 需求生成测试用例。

```python
# 实现要点：
# 1. 每个需求生成至少 1 个正向 + 1 个异常用例
# 2. 用例格式：Given/When/Then
# 3. 每个用例关联 requirement_id
# 4. 生成 CSV/JSON 格式

TC_SYSTEM = "你是QA工程师，请基于PRD需求生成测试用例。"

TC_USER_TEMPLATE = """
需求列表：{requirements}

为每个需求生成测试用例（至少1个正向 + 1个异常）。
输出 JSON：
{{
  "test_cases": [
    {{
      "requirement_id": "REQ-001",
      "title": "用例标题",
      "preconditions": "前置条件",
      "given": "Given...",
      "when": "When...",
      "then": "Then...",
      "type": "positive/negative"
    }}
  ]
}}
"""

class TestCaseGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, requirements: list) -> list:
        """生成测试用例"""
        prompt = TC_USER_TEMPLATE.format(requirements=json.dumps(requirements, ensure_ascii=False))
        result = self.llm.chat_json(TC_SYSTEM, prompt)
        return result.get("test_cases", [])
```

#### 4.4.3 追溯链验证器 (traceability_checker.py)

**职责**：验证评价→发现→需求→测试用例的完整链路。

```python
# 实现要点：
# 1. 优先使用 LLM 验证（使用 TRACEABILITY_VERIFICATION_PROMPT）
# 2. LLM 不可用时使用规则验证
# 3. 检查：每个发现有≥3条评价支撑、需求关联发现、用例关联需求
# 4. 标记断裂点
# 5. 无根据结论标记为"假设"或删除

class TraceabilityChecker:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def check(self, reviews, findings, requirements, test_cases) -> dict:
        """验证可追溯链"""
        # 规则验证
        issues = []

        # 1. 检查发现的评价支撑
        review_ids = {r["review_id"] for r in reviews}
        for f in findings:
            support_ids = f.get("supporting_review_ids", [])
            valid_ids = [rid for rid in support_ids if rid in review_ids]
            if len(valid_ids) < 3:
                issues.append({
                    "item": f"发现: {f.get('title', '')}",
                    "reason": f"支撑评价不足，仅{len(valid_ids)}条（需≥3）",
                    "severity": "high",
                    "suggestion": "标记为假设或补充证据",
                })
                f["is_hypothesis"] = True  # 标记为假设

        # 2. 检查需求关联发现
        finding_ids = {f.get("id", str(i)) for i, f in enumerate(findings)}
        for req in requirements:
            fid = req.get("finding_id")
            if fid not in finding_ids:
                issues.append({
                    "item": f"需求: {req.get('title', '')}",
                    "reason": "未关联到任何发现",
                    "severity": "high",
                    "suggestion": "删除该需求或补充关联",
                })

        # 3. 检查用例关联需求
        req_ids = {r.get("id") for r in requirements}
        for tc in test_cases:
            rid = tc.get("requirement_id")
            if rid not in req_ids:
                issues.append({
                    "item": f"用例: {tc.get('title', '')}",
                    "reason": "未关联到任何需求",
                    "severity": "medium",
                    "suggestion": "删除该用例或补充关联",
                })

        return {
            "issues": issues,
            "passed": len(issues) == 0,
            "summary": f"共{len(issues)}个问题" if issues else "全部验证通过",
        }
```

### 4.5 缓存与离线模块

#### 4.5.1 缓存管理器 (cache_manager.py)

```python
# 实现要点：
# 1. 缓存索引文件：data/cache/cache_index.json
# 2. 评价缓存：data/cache/reviews/{bundle_id}_{timestamp}.json
# 3. 分析缓存：data/cache/analysis/{bundle_id}_{timestamp}.json
# 4. 缓存标识包含：cache_id, bundle_id, collected_at, validity_days, status
# 5. 读取时检查有效期（默认7天）

import os
import json
import hashlib
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self):
        self.cache_dir = os.getenv("CACHE_DIR", "./data/cache")
        self.validity_days = int(os.getenv("CACHE_VALIDITY_DAYS", "7"))

    def save_reviews(self, bundle_id: str, reviews: list) -> dict:
        """保存评价到缓存，返回缓存元数据"""
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        cache_id = f"{bundle_id}_{timestamp}"
        filepath = os.path.join(self.cache_dir, "reviews", f"{cache_id}.json")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False)

        meta = {
            "cache_id": cache_id,
            "bundle_id": bundle_id,
            "collected_at": datetime.now().isoformat(),
            "review_count": len(reviews),
            "validity_days": self.validity_days,
            "status": "active",
            "filepath": filepath,
        }
        self._update_index(meta)
        return meta

    def get_cached_reviews(self, bundle_id: str) -> dict | None:
        """获取最新的缓存评价"""
        index = self._read_index()
        entries = [e for e in index if e["bundle_id"] == bundle_id]
        if not entries:
            return None
        latest = max(entries, key=lambda e: e["collected_at"])
        # 检查有效期
        collected = datetime.fromisoformat(latest["collected_at"])
        if datetime.now() - collected > timedelta(days=self.validity_days):
            latest["status"] = "expired"
        # 读取数据
        filepath = latest["filepath"]
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                reviews = json.load(f)
            return {"meta": latest, "reviews": reviews}
        return None

    def _read_index(self) -> list:
        """读取缓存索引"""
        index_path = os.path.join(self.cache_dir, "cache_index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _update_index(self, meta: dict):
        """更新缓存索引"""
        index = self._read_index()
        index.append(meta)
        index_path = os.path.join(self.cache_dir, "cache_index.json")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
```

#### 4.5.2 可用性检测器 (health_checker.py)

```python
# 实现要点：
# 1. 检测网络：请求 App Store API，超时5秒
# 2. 检测 LLM：检查 API Key 是否配置
# 3. 返回 {network: bool, llm: bool}

class HealthChecker:
    def check_network(self) -> bool:
        """检测网络是否可用"""
        try:
            resp = requests.get(
                "https://itunes.apple.com/lookup?id=839285684",
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def check_llm(self) -> bool:
        """检测 LLM 是否可用"""
        return bool(os.getenv("LLM_API_KEY"))

    def check_all(self) -> dict:
        """检测全部可用性"""
        return {
            "network": self.check_network(),
            "llm": self.check_llm(),
        }
```

### 4.6 API 路由层

#### 4.6.1 路由注册 (routes.py)

```python
# 所有 API 端点注册：
# POST /api/validate-link    → 验证链接，返回应用信息
# POST /api/tasks            → 创建分析任务
# GET  /api/tasks/{id}/progress → 查询任务进度
# GET  /api/tasks/{id}/results  → 查询任务结果
# POST /api/import           → 导入评价数据文件
# GET  /api/tasks/{id}/export   → 导出结果文件
# GET  /api/health           → 检测网络/LLM 可用性
# GET  /api/cache/{bundle_id}   → 查询缓存数据
```

#### 4.6.2 流程编排器 (orchestrator.py)

**核心模块**：编排 10 个阶段的执行顺序。

```python
# 实现要点：
# 1. 接收任务配置（bundle_id, user_goal, filters）
# 2. 按顺序执行 10 个阶段
# 3. 每个阶段更新 stage_tracker 状态
# 4. 任何阶段失败时尝试降级（缓存/降级分析）
# 5. 全部完成后返回完整结果

class PipelineOrchestrator:
    def __init__(self):
        self.llm = LLMClient()
        self.crawler = AppStoreCrawler()
        self.cleaner = ReviewCleaner()
        self.goal_understander = GoalUnderstander(self.llm)
        self.classifier = DynamicClassifier(self.llm)
        self.finding_generator = FindingGenerator(self.llm)
        self.evidence_evaluator = EvidenceEvaluator()
        self.prd_generator = PRDGenerator(self.llm)
        self.test_case_generator = TestCaseGenerator(self.llm)
        self.traceability_checker = TraceabilityChecker(self.llm)
        self.cache_manager = CacheManager()
        self.fallback = FallbackAnalyzer()
        self.tracker = StageTracker()

    def run(self, task_id: str, bundle_id: str, user_goal: str, filters: dict) -> dict:
        """执行完整 10 阶段流程"""
        results = {}

        # 阶段1: 确定分析范围
        self.tracker.update(task_id, "scope_definition", "in_progress")
        goal_info = self.goal_understander.understand(user_goal)
        results["goal_analysis"] = goal_info
        self.tracker.update(task_id, "scope_definition", "completed")

        # 阶段2: 数据收集
        self.tracker.update(task_id, "data_collection", "in_progress")
        try:
            raw_reviews = self.crawler.fetch_reviews(bundle_id)
            self.cache_manager.save_reviews(bundle_id, raw_reviews)
        except Exception:
            # 降级：尝试缓存
            cached = self.cache_manager.get_cached_reviews(bundle_id)
            if cached:
                raw_reviews = cached["reviews"]
                results["data_source"] = "cache"
            else:
                raise RuntimeError("数据采集失败且无缓存可用")
        results["raw_reviews"] = raw_reviews
        self.tracker.update(task_id, "data_collection", "completed")

        # 阶段3: 数据清洗
        self.tracker.update(task_id, "data_cleaning", "in_progress")
        clean_result = self.cleaner.clean(raw_reviews)
        cleaned_reviews = clean_result["cleaned_reviews"]
        results["cleaning_report"] = clean_result
        self.tracker.update(task_id, "data_cleaning", "completed")

        # 阶段4: 动态分类
        self.tracker.update(task_id, "classification", "in_progress")
        if self.llm.is_available():
            categories = self.classifier.classify(
                cleaned_reviews, goal_info["focus_areas"]
            )
        else:
            fallback_result = self.fallback.analyze(cleaned_reviews, user_goal)
            categories = fallback_result["categories"]
            results["is_fallback"] = True
        results["categories"] = categories
        self.tracker.update(task_id, "classification", "completed")

        # 阶段5: 证据评估
        self.tracker.update(task_id, "evidence_evaluation", "in_progress")
        # 先生成发现
        if self.llm.is_available():
            findings = self.finding_generator.generate(
                categories, cleaned_reviews, user_goal
            )
        else:
            findings = fallback_result["findings"]
        # 评估证据
        findings = self.evidence_evaluator.evaluate(findings, cleaned_reviews)
        results["findings"] = findings
        self.tracker.update(task_id, "evidence_evaluation", "completed")

        # 阶段6: PRD 生成
        self.tracker.update(task_id, "prd_generation", "in_progress")
        prd_data = self.prd_generator.generate(findings, user_goal)
        results["prd"] = prd_data
        self.tracker.update(task_id, "prd_generation", "completed")

        # 阶段7: 测试用例生成
        self.tracker.update(task_id, "test_case_generation", "in_progress")
        test_cases = self.test_case_generator.generate(prd_data["requirements"])
        results["test_cases"] = test_cases
        self.tracker.update(task_id, "test_case_generation", "completed")

        # 阶段8: 追溯链验证
        self.tracker.update(task_id, "traceability_verification", "in_progress")
        verification = self.traceability_checker.check(
            cleaned_reviews, findings,
            prd_data["requirements"], test_cases
        )
        results["verification"] = verification
        self.tracker.update(task_id, "traceability_verification", "completed")

        # 阶段9&10: 结果准备（前端展示）
        self.tracker.update(task_id, "result_preparation", "in_progress")
        results["cleaned_reviews"] = cleaned_reviews
        results["task_id"] = task_id
        results["status"] = "completed"
        self.tracker.update(task_id, "result_preparation", "completed")

        return results
```

#### 4.6.3 阶段追踪器 (stage_tracker.py)

```python
# 实现要点：
# 1. 维护每个任务的 10 个阶段状态
# 2. 状态：pending / in_progress / completed / failed
# 3. 每次更新记录时间戳
# 4. 提供查询接口供前端轮询

STAGES = [
    "scope_definition",      # 1. 确定分析范围
    "data_collection",       # 2. 数据收集
    "data_cleaning",         # 3. 数据清洗
    "classification",        # 4. 动态分类
    "evidence_evaluation",   # 5. 证据评估
    "prd_generation",        # 6. PRD生成
    "test_case_generation",  # 7. 测试用例生成
    "traceability_verification",  # 8. 追溯链验证
    "result_preparation",    # 9. 结果准备
    "display",               # 10. 展示（前端负责）
]

class StageTracker:
    def __init__(self):
        self.tasks = {}  # task_id -> {stage: {status, timestamp}}

    def init_task(self, task_id: str):
        """初始化任务阶段状态"""
        self.tasks[task_id] = {
            stage: {"status": "pending", "timestamp": None}
            for stage in STAGES
        }

    def update(self, task_id: str, stage: str, status: str):
        """更新阶段状态"""
        if task_id not in self.tasks:
            self.init_task(task_id)
        self.tasks[task_id][stage] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

    def get_progress(self, task_id: str) -> dict:
        """获取任务进度"""
        if task_id not in self.tasks:
            return {"error": "任务不存在"}
        stages = self.tasks[task_id]
        completed = sum(1 for s in stages.values() if s["status"] == "completed")
        total = len(STAGES)
        current = next((s for s, v in stages.items()
                       if v["status"] == "in_progress"), None)
        return {
            "task_id": task_id,
            "progress_percent": int(completed / total * 100),
            "current_stage": current,
            "stages": [{"name": s, "status": v["status"]}
                      for s, v in stages.items()],
        }
```

---

## 5. 前端实现方案

### 5.1 页面结构与路由

单页应用（SPA），通过状态切换不同视图：

```
状态1: input      → 链接输入 + 目标配置视图
状态2: preview    → 应用信息预览 + 确认开始
状态3: progress   → 进度追踪面板
状态4: results    → 结果展示（多标签页）
```

### 5.2 核心组件实现

#### 5.2.1 HomePage.tsx（主页面容器）

```tsx
// 实现要点：
// 1. 管理全局状态：currentView, taskData, progressData, resultsData
// 2. 根据状态渲染不同子组件
// 3. 处理 API 调用和错误

import { useState } from 'react';
import LinkInput from './components/LinkInput';
import AppPreview from './components/AppPreview';
import ProgressTracker from './components/ProgressTracker';
import ResultsView from './components/ResultsView';
import { useAnalysisTask } from './hooks/useAnalysisTask';

type View = 'input' | 'preview' | 'progress' | 'results';

export default function HomePage() {
  const [view, setView] = useState<View>('input');
  const { task, validateLink, startAnalysis, pollProgress, getResults } = useAnalysisTask();

  // 视图切换逻辑
  // view='input'  → <LinkInput onValidate={validateLink} onSuccess={() => setView('preview')} />
  // view='preview'→ <AppPreview info={task.appInfo} onStart={startAnalysis} />
  // view='progress'→ <ProgressTracker task={task} onComplete={() => setView('results')} />
  // view='results'→ <ResultsView data={task.results} />
}
```

#### 5.2.2 LinkInput.tsx（链接输入）

```tsx
// 实现要点：
// 1. 输入框 + 验证按钮
// 2. 客户端正则验证
// 3. 调用 /api/validate-link
// 4. 成功后显示应用预览卡片
// 5. 错误时显示友好提示
```

#### 5.2.3 GoalInput.tsx（分析目标输入）

```tsx
// 实现要点：
// 1. 自由文本输入框（textarea）
// 2. 提供示例提示文字（非预设选项）
// 3. 示例："关注订阅转化率和用户付费体验"
// 4. 留空时提示"未指定目标，将进行全面分析"
```

#### 5.2.4 ProgressTracker.tsx（进度追踪面板）

```tsx
// 实现要点：
// 1. 轮询 /api/tasks/{id}/progress（每2秒）
// 2. 显示 10 个阶段的进度条
// 3. 每个阶段显示：名称、状态图标、耗时
// 4. 当前阶段高亮，已完成阶段打勾
// 5. 显示进度百分比
// 6. 若使用缓存，显示 CacheBanner
// 7. 完成后自动切换到结果视图
```

#### 5.2.5 ResultsView.tsx（结果展示）

```tsx
// 实现要点：
// 1. 标签页切换：原始评价 | 清洗数据 | 分类结果 | 发现 | PRD | 测试用例 | 追溯链
// 2. 原始评价：ReviewTable 表格
// 3. 分类结果：CategoryChart 饼图/柱状图
// 4. 发现：FindingCards 卡片列表
// 5. PRD：PRDViewer Markdown 渲染
// 6. 测试用例：TestCaseTable 表格
// 7. 追溯链：TraceabilityView 树形/链路图
// 8. 顶部显示 ExportButton
```

#### 5.2.6 CacheBanner.tsx（缓存标识横幅）

```tsx
// 实现要点：
// 1. 当 is_using_cache=true 时显示
// 2. 黄色背景横幅
// 3. 显示缓存时间、评价数量、有效期
// 4. 提供"使用最新数据"按钮
```

#### 5.2.7 DataImport.tsx（数据导入）

```tsx
// 实现要点：
// 1. 文件上传区域（支持 .json / .csv）
// 2. 调用 /api/import
// 3. 显示导入统计（总数、有效数、无效数）
// 4. 提供示例文件下载链接
// 5. 导入成功后进入分析流程
```

### 5.3 状态管理

使用自定义 Hooks 管理状态，不引入额外状态库：

```typescript
// hooks/useAnalysisTask.ts 管理核心状态：
interface TaskState {
  taskId: string | null;
  status: 'idle' | 'validating' | 'ready' | 'running' | 'completed' | 'error';
  appInfo: AppInfo | null;
  progress: ProgressData | null;
  results: AnalysisResults | null;
  isUsingCache: boolean;
  error: string | null;
}
```

### 5.4 API 对接层

```typescript
// services/api.ts 封装所有后端调用：
const API_BASE = 'http://localhost:8000/api';

export const api = {
  validateLink: (url: string) => fetch(`${API_BASE}/validate-link`, {method: 'POST', body: JSON.stringify({url})}),
  createTask: (bundleId: string, userGoal: string, filters: any) => fetch(`${API_BASE}/tasks`, {...}),
  getProgress: (taskId: string) => fetch(`${API_BASE}/tasks/${taskId}/progress`),
  getResults: (taskId: string) => fetch(`${API_BASE}/tasks/${taskId}/results`),
  importData: (file: File) => fetch(`${API_BASE}/import`, {method: 'POST', body: formData}),
  exportResults: (taskId: string, format: string) => fetch(`${API_BASE}/tasks/${taskId}/export?format=${format}`),
  checkHealth: () => fetch(`${API_BASE}/health`),
};
```

### 5.5 TypeScript 类型定义

```typescript
// types/index.ts
interface Review {
  review_id: string;
  author: string;
  rating: number;
  title: string;
  content: string;
  review_date: string;
  version: string;
}

interface Category {
  name: string;
  description: string;
  review_ids: string[];
  sentiment: 'positive' | 'negative' | 'neutral' | 'mixed';
  key_points: string[];
}

interface Finding {
  title: string;
  description: string;
  evidence_strength: 'strong' | 'medium' | 'weak';
  supporting_review_ids: string[];
  representative_quotes: string[];
  suggested_action: string;
  is_positive: boolean;
  is_contradictory: boolean;
  is_hypothesis?: boolean;
}

interface Requirement {
  id: string;
  finding_id: string;
  title: string;
  user_story: string;
  priority: 'P0' | 'P1' | 'P2';
  version_suggestion: 'V1' | 'V2';
}

interface TestCase {
  requirement_id: string;
  title: string;
  preconditions: string;
  given: string;
  when: string;
  then: string;
  type: 'positive' | 'negative';
}

interface ProgressData {
  task_id: string;
  progress_percent: number;
  current_stage: string;
  stages: { name: string; status: string }[];
}
```

---

## 6. 数据库设计与初始化

### 6.1 SQLite 表结构 (database.py)

```python
# 实现要点：
# 1. 使用 Python 标准库 sqlite3（无需额外依赖）
# 2. 数据库路径：data/db/app_review.db
# 3. 自动建表

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "./data/db/app_review.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_task (
    id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL,
    app_name TEXT,
    user_goal TEXT,
    rating_filter TEXT,
    time_range TEXT,
    version_filter TEXT,
    status TEXT DEFAULT 'pending',
    is_using_cache INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS review (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    author TEXT,
    rating INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    review_date TEXT NOT NULL,
    version TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS category (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    review_count INTEGER,
    sentiment TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS finding (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    category_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    evidence_strength TEXT,
    supporting_review_ids TEXT,  -- JSON array
    is_hypothesis INTEGER DEFAULT 0,
    is_contradictory INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS requirement (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    finding_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT,
    version_suggestion TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS test_case (
    id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    title TEXT NOT NULL,
    preconditions TEXT,
    steps TEXT,
    expected_result TEXT,
    case_type TEXT,
    FOREIGN KEY (requirement_id) REFERENCES requirement(id)
);
"""

def init_db():
    """初始化数据库，创建所有表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.close()
```

### 6.2 Pydantic 数据模型 (schemas.py)

```python
# 实现要点：
# 1. 定义所有 API 请求/响应的 Pydantic 模型
# 2. 用于 FastAPI 自动生成文档和参数校验

from pydantic import BaseModel

class ValidateLinkRequest(BaseModel):
    url: str

class ValidateLinkResponse(BaseModel):
    valid: bool
    bundle_id: str | None
    app_info: dict | None
    error: str | None

class CreateTaskRequest(BaseModel):
    bundle_id: str
    user_goal: str = ""
    config: dict = {}

class CreateTaskResponse(BaseModel):
    task_id: str
    status: str

class ProgressResponse(BaseModel):
    task_id: str
    status: str
    current_stage: str | None
    progress_percent: int
    is_using_cache: bool
    stages: list

class ResultsResponse(BaseModel):
    task_id: str
    status: str
    data_source: str  # "live" | "cache" | "import"
    deliverables: dict

class ImportResponse(BaseModel):
    import_id: str
    status: str
    statistics: dict
```

---

## 7. 全流程实现顺序

> 这是 AI 代理实现项目时应该遵循的编码顺序。每个步骤都有明确的输入、输出和验证标准。

### 步骤 1: 项目初始化与目录创建

**操作**：
1. 创建项目根目录结构（按第2节目录结构创建所有文件夹）
2. 创建 `backend/` 和 `frontend/` 目录
3. 创建 `data/cache/`, `data/db/`, `data/exports/`, `data/samples/` 目录

**验证**：目录结构完整，`ls` 可见所有目录。

### 步骤 2: 后端基础框架

**操作**：
1. 创建 `backend/requirements.txt`（按第3.1节）
2. 创建 `backend/.env.example`（按第3.3节）
3. 创建 `backend/app/config.py`：读取环境变量
4. 创建 `backend/app/main.py`：FastAPI 应用入口，配置 CORS
5. 创建 `backend/app/models/database.py`：SQLite 初始化（按第6.1节）
6. 创建 `backend/app/models/schemas.py`：Pydantic 模型（按第6.2节）
7. 创建 `backend/app/utils/logger.py`：日志配置

**验证**：`python backend/run.py` 能启动服务，访问 `http://localhost:8000/docs` 可见 Swagger 文档。

### 步骤 3: 数据采集层实现

**操作**：
1. 实现 `link_parser.py`（按第4.1.1节）
2. 实现 `app_store.py`（按第4.1.2节）
3. 实现 `file_importer.py`（按第4.1.3节）
4. 实现 API 路由 `validate.py`：`POST /api/validate-link`
5. 实现 API 路由 `import_data.py`：`POST /api/import`

**验证**：
- 输入示例链接 `https://apps.apple.com/us/app/workout-for-women-home-gym/id839285684`，返回应用信息
- 爬虫能获取至少 1 页评价数据（需联网）

### 步骤 4: 数据清洗层实现

**操作**：
1. 实现 `review_cleaner.py`（按第4.2节）
2. 在 API 中集成清洗流程

**验证**：
- 输入含重复数据的评价列表，去重后数量减少
- HTML 标签被正确移除
- 日期格式标准化为 YYYY-MM-DD

### 步骤 5: 缓存与离线模块

**操作**：
1. 实现 `cache_manager.py`（按第4.5.1节）
2. 实现 `health_checker.py`（按第4.5.2节）
3. 在数据采集后自动保存缓存
4. 实现 API 路由 `GET /api/health` 和 `GET /api/cache/{bundle_id}`

**验证**：
- 采集数据后 `data/cache/reviews/` 下有 JSON 文件
- `cache_index.json` 有索引记录
- 断网后 `GET /api/health` 返回 `{network: false}`

### 步骤 6: LLM 分析引擎实现

**操作**：
1. 实现 `llm_client.py`（按第4.3.1节）
2. 实现 `goal_understander.py`（按第4.3.2节）
3. 实现 `classifier.py`（按第4.3.3节）
4. 实现 `finding_generator.py`（按第4.3.4节）
5. 实现 `evidence_evaluator.py`（按第4.3.5节）
6. 实现 `fallback_analyzer.py`（按第4.3.6节）

**验证**（需配置 LLM API Key）：
- 输入目标"关注订阅转化率"，返回包含 focus_areas 的 JSON
- 输入 30 条评价，返回动态分类结果（类别名非预设）
- 生成发现含 evidence_strength 和 supporting_review_ids
- 无 API Key 时降级模式能运行

### 步骤 7: 文档生成层实现

**操作**：
1. 实现 `prd_generator.py`（按第4.4.1节）
2. 实现 `test_case_generator.py`（按第4.4.2节）
3. 实现 `traceability_checker.py`（按第4.4.3节）
4. 实现 `exporter.py`：Markdown/CSV 导出工具

**验证**：
- PRD 生成后每个需求关联到 finding_id
- 测试用例有 Given/When/Then 结构
- 追溯链验证能检测到断裂点
- 导出的 Markdown 文件可正常打开

### 步骤 8: 流程编排层实现

**操作**：
1. 实现 `stage_tracker.py`（按第4.6.3节）
2. 实现 `orchestrator.py`（按第4.6.2节）
3. 实现 API 路由 `tasks.py`：
   - `POST /api/tasks`：创建任务并启动编排器
   - `GET /api/tasks/{id}/progress`：查询进度
   - `GET /api/tasks/{id}/results`：查询结果
4. 实现 API 路由 `export.py`：`GET /api/tasks/{id}/export`

**验证**：
- 创建任务后能返回 task_id
- 轮询 progress 能看到阶段推进
- 完成后 results 包含所有交付物
- 某阶段失败时能降级而非崩溃

### 步骤 9: 前端项目初始化

**操作**：
1. 用 Vite 创建 React + TypeScript 项目
2. 安装依赖（按第3.2节 package.json）
3. 配置 TailwindCSS
4. 配置 vite.config.ts（代理 /api 到 localhost:8000）
5. 创建 `types/index.ts`（按第5.5节）
6. 创建 `services/api.ts`（按第5.4节）

**验证**：`npm run dev` 启动前端，页面可访问。

### 步骤 10: 前端组件实现

**操作**：
1. 实现 `LinkInput.tsx`（按第5.2.2节）
2. 实现 `AppPreview.tsx`：应用信息卡片
3. 实现 `GoalInput.tsx`（按第5.2.3节）
4. 实现 `FilterConfig.tsx`：评分/时间/版本筛选
5. 实现 `HomePage.tsx`（按第5.2.1节）：状态管理
6. 实现 `useAnalysisTask.ts` Hook（按第5.3节）

**验证**：
- 输入链接后显示应用信息卡片
- 目标输入框可自由输入
- 点击开始后状态切换到 progress

### 步骤 11: 前端进度与结果展示

**操作**：
1. 实现 `ProgressTracker.tsx`（按第5.2.4节）
2. 实现 `useProgressPoll.ts` Hook：每 2 秒轮询进度
3. 实现 `CacheBanner.tsx`（按第5.2.6节）
4. 实现 `ResultsView.tsx`（按第5.2.5节）
5. 实现 `ReviewTable.tsx`：评价数据表格
6. 实现 `CategoryChart.tsx`：Recharts 饼图
7. 实现 `FindingCards.tsx`：发现卡片列表
8. 实现 `PRDViewer.tsx`：Markdown 渲染
9. 实现 `TestCaseTable.tsx`：测试用例表格
10. 实现 `TraceabilityView.tsx`：追溯链可视化
11. 实现 `ExportButton.tsx`：导出按钮
12. 实现 `DataImport.tsx`（按第5.2.7节）

**验证**：
- 进度面板实时更新阶段状态
- 结果页各标签页内容正确
- 导出按钮能下载文件
- 数据导入组件能上传并解析文件

### 步骤 12: 样本数据与缓存预置

**操作**：
1. 创建 `data/samples/sample_reviews.json`：包含 50-100 条样本评价
2. 运行一次完整流程生成缓存数据
3. 将缓存数据标记为 "sample_cache"
4. 确保 `data/cache/` 下有可用的缓存数据

**验证**：断网状态下仍能使用缓存数据完成分析流程。

### 步骤 13: 集成测试与错误处理

**操作**：
1. 端到端测试：输入链接 → 完整流程 → 查看结果
2. 异常测试：无效链接、网络断开、无 LLM Key
3. 完善错误提示和重试逻辑
4. 确保 10 个阶段每个都有错误处理

**验证**：
- 正常流程端到端通过
- 无效链接显示友好错误
- 断网时提示使用缓存
- 无 LLM 时降级分析正常

### 步骤 14: 文档与部署配置

**操作**：
1. 创建 `README.md`：运行指令、环境配置、数据获取说明
2. 创建 `docker-compose.yml`（可选）
3. 创建 `.env.example`
4. 确保 `.env` 在 `.gitignore` 中

**验证**：新开发者按 README 能在 10 分钟内运行项目。

---

## 8. 端到端验证方案

### 8.1 正常流程验证

```
1. 启动后端：python backend/run.py
2. 启动前端：cd frontend && npm run dev
3. 打开 http://localhost:5173
4. 输入链接：https://apps.apple.com/us/app/workout-for-women-home-gym/id839285684
5. 确认应用信息显示
6. 输入目标："关注订阅转化率和用户付费体验"
7. 点击"开始分析"
8. 观察 10 个阶段逐步完成
9. 查看结果：评价表格、分类图表、发现卡片、PRD、测试用例、追溯链
10. 点击导出，下载文件
```

### 8.2 离线模式验证

```
1. 不配置 LLM_API_KEY
2. 输入链接，开始分析
3. 验证：进度面板显示"基础分析模式"
4. 结果中分类为关键词统计（非 LLM 动态分类）
5. 结果中 is_fallback=true
```

### 8.3 缓存模式验证

```
1. 先正常运行一次，生成缓存
2. 断开网络
3. 再次分析同一应用
4. 验证：显示 CacheBanner 横幅
5. 验证：使用缓存数据完成分析
```

### 8.4 数据导入验证

```
1. 准备 JSON 文件（包含 50 条评价）
2. 点击"导入数据"按钮
3. 上传文件
4. 验证：显示导入统计
5. 验证：进入分析流程并完成
```

### 8.5 追溯链验证

```
1. 完成正常分析流程
2. 查看追溯链视图
3. 验证：每个发现有关联的评价
4. 验证：每个需求有关联的发现
5. 验证：每个测试用例有关联的需求
6. 验证：无根据结论被标记为"假设"
```

---

## 9. 部署与运行

### 9.1 本地开发运行

```bash
# 1. 克隆项目
git clone <repo-url>
cd app-eval-insight

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env，填入 LLM_API_KEY（可选，不填则使用降级模式）

# 3. 安装后端依赖
cd backend
pip install -r requirements.txt

# 4. 初始化数据库
python -c "from app.models.database import init_db; init_db()"

# 5. 启动后端
python run.py
# 后端运行在 http://localhost:8000

# 6. 安装前端依赖
cd ../frontend
npm install

# 7. 启动前端
npm run dev
# 前端运行在 http://localhost:5173

# 8. 打开浏览器访问 http://localhost:5173
```

### 9.2 Docker 运行（可选）

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

### 9.3 关键配置说明

| 配置项 | 必填 | 说明 |
|--------|------|------|
| LLM_API_KEY | 否 | LLM API 密钥，不配置则使用降级模式 |
| LLM_BASE_URL | 否 | LLM API 地址，默认 OpenAI |
| LLM_MODEL | 否 | 模型名称，默认 gpt-4o-mini |
| CACHE_VALIDITY_DAYS | 否 | 缓存有效期，默认 7 天 |

---

## 附录：实现检查清单

- [ ] 目录结构完整创建
- [ ] 后端 FastAPI 启动正常，Swagger 文档可访问
- [ ] 链接验证接口可用，能解析 App Store 链接
- [ ] RSS 爬虫能采集评价数据（联网时）
- [ ] 数据清洗正确去重和格式化
- [ ] 缓存机制正常工作（保存/读取/标识）
- [ ] 网络/LLM 可用性检测正常
- [ ] LLM 目标理解模块工作正常
- [ ] LLM 动态分类生成非预设类别
- [ ] 发现生成含证据强度和支撑评价
- [ ] 证据评估检测矛盾反馈
- [ ] PRD 生成含需求条目和版本拆分
- [ ] 测试用例生成 Given/When/Then 格式
- [ ] 追溯链验证检测断裂点
- [ ] 无 LLM 时降级分析正常工作
- [ ] 10 阶段编排器按序执行
- [ ] 前端链接输入和验证功能正常
- [ ] 前端进度追踪实时更新
- [ ] 前端结果展示所有交付物
- [ ] 前端导出功能正常下载
- [ ] 前端数据导入功能正常
- [ ] 前端缓存标识横幅正确显示
- [ ] 样本数据预置完成
- [ ] 端到端流程完整通过
- [ ] README 文档编写完成
