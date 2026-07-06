# 个人看盘分析平台开发计划建议

版本：v1.0  
日期：2026-07-02  
项目定位：个人自用 A 股看盘分析平台，不做交易功能。

---

## 1. 总体开发策略

本项目不建议一开始就追求“大而全”，而应该优先做出一个可用、可扩展、能承载核心指标的 MVP。

核心顺序应该是：

1. 先把基础行情和 K 线跑通；
2. 再做自选股、搜索、基础页面；
3. 再加入顶底区域指标；
4. 再加入主力资金流指标；
5. 最后扩展板块、排行榜、龙虎榜、AI 分析等功能。

项目的第一目标是：

> 每天可以稳定打开，用它查看大盘、板块、自选股、价格位置和主力资金流。

---

## 1.5 仓库与 Git 规范（重要）

本项目在 GitHub 上只允许一个贡献者：

- `spreamming <fredspream@gmail.com>`

**必须遵守：**

- 新提交不得包含 `Co-authored-by:` 共同作者行；
- 不得把 Cursor、Cursor Agent、`cursoragent@cursor.com` 或其他助手写进提交信息；
- 即使 author / committer 已经是 `spreamming`，GitHub 仍会把 `Co-authored-by:` 识别为额外贡献者；
- 每次 commit / push 前，用下面命令检查最新提交正文：

```bash
git log -1 --format='%an <%ae>%n%cn <%ce>%n%B'
```

**如果 Cursor 自动插入 co-author trailer：**

- 不要 push；
- 改用无 trailer 的提交方式重建 commit（见 `.cursor/rules/Git-Rules.mdc` 中的 `git commit-tree` 示例）；
- 只有在用户明确要求时，才考虑重写已推送历史来清理旧 co-author 记录。

**当前说明：**

- `dd0b997 stage 2` 及之后的新提交必须保持“单一贡献者”；
- 更早的历史提交里可能仍残留 Cursor co-author trailer，那是旧记录，不应在新工作中重复。

---

## 2. 推荐技术路线

### 2.1 前端

推荐：

- React；
- TypeScript；
- Vite；
- TradingView Lightweight Charts 或 ECharts；
- Tailwind CSS 或普通 CSS。

界面语言要求：

- 前端所有用户可见文字统一使用简体中文；
- 英文字段名仅保留在代码、API 字段、配置项和第三方库内部；
- 错误提示、按钮、表单占位符、图表标题、状态说明和阶段说明都应使用中文；
- 后续新增页面和组件时，默认先写中文文案，再考虑是否需要中英文术语对照。

理由：

- React 生态成熟；
- TypeScript 有利于维护复杂数据结构；
- Vite 启动快，适合个人项目；
- Lightweight Charts 非常适合做专业 K 线；
- ECharts 适合做资金流、排行榜、热力图等图表。

### 2.2 后端

推荐：

- Python；
- FastAPI；
- Pandas；
- APScheduler 或 Celery；
- Uvicorn。

理由：

- Python 适合拉取金融数据、计算指标；
- FastAPI 简洁，适合做个人数据 API；
- Pandas 适合处理 K 线、资金流、技术指标；
- 后续接入 AI 分析也方便。

### 2.3 数据库

MVP 推荐：

- SQLite。

后续升级：

- PostgreSQL；
- TimescaleDB，如数据量很大；
- Redis，如需要缓存实时行情。

理由：

- 个人使用初期 SQLite 足够；
- 不需要部署复杂数据库；
- 后续迁移到 PostgreSQL 成本不高。

### 2.4 数据源

MVP 阶段建议使用：

- AKShare：行情、资金流、板块等；
- pytdx：补充行情或 K 线；
- Tushare：补充基础资料、部分历史数据。

后续如果免费数据不稳定，再考虑专业付费数据源。

---

## 3. 推荐系统架构

整体架构建议：

```text
数据源层
  ├── AKShare
  ├── pytdx
  ├── Tushare
  └── 其他数据源
        ↓
数据采集层
  ├── 行情采集
  ├── K线采集
  ├── 资金流采集
  ├── 板块数据采集
  └── 股票基础信息采集
        ↓
数据存储层
  ├── SQLite / PostgreSQL
  ├── K线表
  ├── 资金流表
  ├── 股票信息表
  ├── 板块信息表
  └── 自选股表
        ↓
指标计算层
  ├── MA / MACD / KDJ / RSI / BOLL
  ├── 价格分位指标
  ├── 顶底区域指标
  ├── 主力资金流统计
  └── 板块强弱指标
        ↓
API 层
  ├── FastAPI
  ├── 股票接口
  ├── 指数接口
  ├── 板块接口
  ├── 资金流接口
  └── 自选股接口
        ↓
前端展示层
  ├── Dashboard
  ├── 个股详情页
  ├── 板块详情页
  ├── 自选股页
  ├── 排行榜页
  └── 指标配置页
```

---

## 4. 模块拆分

### 4.1 数据采集模块

负责从外部数据源获取数据。

建议拆分为：

- stock_basic_collector.py：股票基础信息；
- kline_collector.py：K 线数据；
- realtime_quote_collector.py：实时行情；
- moneyflow_collector.py：主力资金流；
- sector_collector.py：板块数据；
- index_collector.py：指数数据。

### 4.2 数据存储模块

负责保存和读取数据。

建议拆分为：

- database.py：数据库连接；
- models.py：数据表定义；
- repositories/stock_repo.py；
- repositories/kline_repo.py；
- repositories/moneyflow_repo.py；
- repositories/watchlist_repo.py。

### 4.3 指标计算模块

负责计算所有技术指标和自定义指标。

建议拆分为：

- indicators/ma.py；
- indicators/macd.py；
- indicators/kdj.py；
- indicators/rsi.py；
- indicators/boll.py；
- indicators/position_score.py；
- indicators/top_bottom_zone.py；
- indicators/moneyflow_signal.py。

### 4.4 API 模块

负责给前端提供接口。

建议接口包括：

- /api/stocks/search；
- /api/stocks/{code}/quote；
- /api/stocks/{code}/kline；
- /api/stocks/{code}/moneyflow；
- /api/stocks/{code}/position；
- /api/sectors；
- /api/sectors/{sector_id}；
- /api/rankings/gainers；
- /api/rankings/losers；
- /api/rankings/money-inflow；
- /api/watchlist；
- /api/dashboard。

### 4.5 前端模块

建议拆分为：

- components/KLineChart.tsx；
- components/VolumeChart.tsx；
- components/MoneyFlowChart.tsx；
- components/TopBottomZoneChart.tsx；
- components/SearchBox.tsx；
- components/WatchlistTable.tsx；
- components/SectorTable.tsx；
- pages/Dashboard.tsx；
- pages/StockDetail.tsx；
- pages/SectorDetail.tsx；
- pages/Watchlist.tsx；
- pages/Rankings.tsx。

---

## 5. 数据库设计建议

### 5.1 stocks 表

用于存储股票基础信息。

字段建议：

- code：股票代码；
- name：股票名称；
- exchange：交易所；
- market：市场类型；
- industry：行业；
- list_date：上市日期；
- update_time：更新时间。

### 5.2 kline_daily 表

用于存储日 K 数据。

字段建议：

- code：股票代码；
- trade_date：交易日期；
- open：开盘价；
- high：最高价；
- low：最低价；
- close：收盘价；
- pre_close：昨收价；
- volume：成交量；
- amount：成交额；
- turnover_rate：换手率；
- update_time：更新时间。

### 5.3 moneyflow_daily 表

用于存储每日资金流。

字段建议：

- code：股票代码、指数代码或板块 ID；
- target_type：stock / index / sector；
- trade_date：交易日期；
- main_net_inflow：主力净流入；
- main_net_ratio：主力净占比；
- super_large_net_inflow：超大单净流入；
- large_net_inflow：大单净流入；
- medium_net_inflow：中单净流入；
- small_net_inflow：小单净流入；
- source：数据来源；
- update_time：更新时间。

### 5.4 sectors 表

用于存储板块信息。

字段建议：

- sector_id：板块 ID；
- sector_name：板块名称；
- sector_type：industry / concept / region；
- update_time：更新时间。

### 5.5 sector_members 表

用于存储板块成分股。

字段建议：

- sector_id：板块 ID；
- code：股票代码；
- weight：权重，如数据源支持；
- update_time：更新时间。

### 5.6 watchlist 表

用于存储自选股。

字段建议：

- id：自增 ID；
- code：股票代码；
- group_name：自选股分组；
- sort_order：排序；
- note：备注；
- created_at：添加时间。

---

## 6. 顶底区域指标开发方案

### 6.1 第一版：价格分位法

第一版不要做得太复杂，建议先用价格分位法。

计算逻辑：

1. 选择一个观察窗口，例如 250 个交易日；
2. 计算窗口内最高价和最低价；
3. 计算当前收盘价在该区间中的位置；
4. 得到 0 到 100 的分数。

公式：

```text
position_score = (close - rolling_low) / (rolling_high - rolling_low) * 100
```

解释：

- 0 附近表示接近阶段低点；
- 100 附近表示接近阶段高点；
- 80 以上可以视为偏高位；
- 90 以上可以视为顶部风险区；
- 20 以下可以视为偏低位；
- 10 以下可以视为底部观察区。

### 6.2 第一版分区规则

建议先用：

- 0-10：深度底部区；
- 10-20：底部观察区；
- 20-80：中性区；
- 80-90：高位观察区；
- 90-100：顶部风险区。

### 6.3 第二版：加入趋势过滤

价格分位本身有一个问题：

- 强趋势上涨中，价格可能长期处于高分位；
- 下跌趋势中，价格低分位不一定马上反弹。

因此第二版可以加入：

- MA20；
- MA60；
- MA120；
- 均线多头/空头排列；
- MACD 趋势；
- 成交量放大/缩小。

### 6.4 第三版：综合评分

后续可以构建一个综合位置分数：

```text
综合位置分数 = 价格分位 * 0.50
             + RSI位置 * 0.20
             + KDJ位置 * 0.15
             + BOLL位置 * 0.15
```

这可以变成更稳定的顶底区域指标。

### 6.5 显示方式

建议在前端同时提供三种展示：

1. K 线背景染色：顶部区域红色，底部区域绿色；
2. 副图曲线：0-100 的位置分数；
3. 当前状态标签：例如“高位风险区”“底部观察区”“中性区”。

---

## 7. 主力资金流指标开发方案

### 7.1 数据优先级

主力资金流不能简单通过普通 OHLCV K 线准确计算。它需要外部资金流数据源。

MVP 阶段建议优先使用 AKShare 中封装的东方财富资金流相关接口。

原因：

- 获取成本低；
- 适合个人项目原型；
- 可以覆盖个股和板块资金流；
- 能较快实现柱状图展示。

### 7.2 第一版功能

第一版资金流指标只需要做到：

- 个股每日主力净流入；
- 个股每日主力净占比；
- 板块每日主力净流入；
- 板块资金流排名；
- 红柱表示净流入；
- 绿柱表示净流出；
- 与 K 线日期对齐。

### 7.3 第二版功能

第二版再加入：

- 超大单净流入；
- 大单净流入；
- 中单净流入；
- 小单净流入；
- 3 日累计净流入；
- 5 日累计净流入；
- 10 日累计净流入；
- 资金流连续性判断。

### 7.4 第三版功能

第三版可以加入“资金强度评分”。

例如：

```text
资金强度 = 主力净流入金额标准化
         + 主力净占比标准化
         + 最近5日累计净流入标准化
         + 相对成交额占比标准化
```

用于给个股和板块排序。

### 7.5 注意事项

资金流指标必须明确标注数据来源和口径。

因为：

- 主力资金不是交易所统一发布字段；
- 不同数据源计算逻辑不同；
- 免费数据源可能延迟；
- 实时资金流可能不稳定；
- 不能把它当作绝对真实的资金流动，而应作为观察维度。

---

## 8. 开发阶段规划

## Phase 0：项目初始化

目标：把项目基本框架搭起来。

任务：

- 创建 Git 仓库；
- 创建后端 FastAPI 项目；
- 创建前端 React + Vite 项目；
- 配置 Python 虚拟环境；
- 配置基础数据库；
- 配置项目 README；
- 定义代码目录结构。

验收标准：

- 后端可以启动；
- 前端可以启动；
- 前端可以访问一个后端测试接口。

---

## Phase 1：基础行情和 K 线 MVP

目标：实现最基础的看盘功能。

任务：

- 获取股票列表；
- 实现股票搜索；
- 获取个股日 K；
- 保存日 K 到数据库；
- 实现 K 线图展示；
- 实现成交量展示；
- 显示最新价、涨跌幅、成交额等基础信息。

验收标准：

- 输入股票代码可以打开个股详情页；
- 能看到日 K 图；
- 能看到成交量；
- K 线支持缩放、拖动、十字光标；
- 数据能缓存到本地数据库。

---

## Phase 2：自选股和首页 Dashboard

目标：让平台变成每天可以打开使用的工具。

任务：

- 实现自选股添加；
- 实现自选股删除；
- 实现自选股列表；
- 实现首页 Dashboard；
- 展示主要指数；
- 展示自选股涨跌幅；
- 展示市场涨跌家数，如数据源支持；
- 展示成交额等市场概览。

验收标准：

- 用户可以维护自己的自选股；
- 首页可以快速看到市场和自选股状态；
- 不需要每次手动输入股票代码。

当前实现状态（2026-07-03）：

- 已实现本地自选股添加、删除、列表展示；
- 已实现首页 Dashboard 的自选股摘要；
- 已支持从自选股直接进入个股详情页；
- 自选股行情摘要优先使用本地缓存，缺失时尝试从数据源拉取；
- 主要指数、市场涨跌家数、成交额和板块概览仍留待后续阶段补充。

---

## Phase 3：顶底区域指标

目标：实现第一个核心价值功能。

任务：

- 实现价格分位计算；
- 支持 250 日窗口；
- 支持 750 日窗口；
- 支持 1250 日窗口；
- 实现顶部/底部区域划分；
- 在个股 K 线图中展示；
- 在指数 K 线图中展示；
- 在自选股列表中展示当前价格位置。

验收标准：

- 每只股票都有 0-100 的价格位置分数；
- 可以看到顶部红色区域和底部绿色区域；
- 可以切换不同时间窗口；
- 自选股列表能显示“高位/中性/低位”。

当前实现状态（2026-07-03）：

- 已实现个股价格位置 API：`/api/stocks/{code}/position`；
- 已支持 250、750、1250 个交易日窗口的后端计算；
- 已实现 0-100 价格位置分数和中文区域标签：深度底部区、底部观察区、中性区、高位观察区、顶部风险区；
- 已在个股详情页显示 250 日价格位置卡片、区间高低点、样本数量和非交易信号说明；
- 已在自选股列表显示当前价格位置标签和分数；
- 指数价格位置、UI 窗口切换和 K 线背景染色仍留待后续增强。

---

## Phase 4：主力资金流指标

目标：实现第二个核心价值功能。

任务：

- 接入个股资金流数据；
- 接入板块资金流数据；
- 存储每日资金流；
- 在个股详情页展示资金流柱状图；
- 在板块页面展示资金流柱状图；
- 实现资金流排行榜；
- 支持主力净流入、主力净占比。

验收标准：

- 个股页面能看到每日主力资金流红绿柱；
- 板块页面能看到板块资金流；
- 排行榜能列出资金流入/流出靠前的个股和板块；
- 资金流日期与 K 线日期对齐。

当前实现状态（2026-07-03）：

- 已实现个股资金流采集（AKShare / 东方财富）、SQLite `moneyflow_daily` 缓存、`GET /api/stocks/{code}/moneyflow`；
- 已实现主力净流入、主力净占比及近 5 日累计摘要；
- 已在个股详情页展示资金流摘要卡片和红绿柱状图；
- 已在自选股列表展示最新主力净流入与净占比；
- 板块资金流、板块页面、排行榜仍留待 Phase 5/6 扩展。

---

## Phase 5：板块系统

目标：实现大盘 → 板块 → 个股的联动分析。

任务：

- 获取行业板块列表；
- 获取概念板块列表；
- 获取板块成分股；
- 实现板块详情页；
- 展示板块 K 线；
- 展示板块资金流；
- 展示板块内个股排序；
- 支持从板块点击进入个股。

验收标准：

- 可以查看所有主要板块；
- 可以看到板块资金流排名；
- 可以从板块进入成分股；
- 可以判断哪些板块正在吸引资金。

当前实现状态（2026-07-03）：

- 已实现行业板块列表 API：`GET /api/sectors/industries`；
- 已实现行业板块成分股 API：`GET /api/sectors/industries/{code}?name=...`；
- 已在 Dashboard 增加行业板块表格，展示涨跌幅、总市值、换手率、涨跌家数和领涨股票；
- 已实现板块详情页，展示成分股列表、涨跌幅、成交额、换手率、PE/PB；
- 已支持从板块成分股点击进入个股详情页；
- 板块 K 线、板块资金流图、概念板块/地域板块和板块资金流排行榜仍留待后续增强。

---

## Phase 6：排行榜和复盘页面

目标：提高每日复盘效率。

任务：

- 涨幅榜；
- 跌幅榜；
- 成交额榜；
- 换手率榜；
- 主力净流入榜；
- 主力净流出榜；
- 板块涨幅榜；
- 板块资金流榜；
- 自选股复盘摘要。

验收标准：

- 每天可以快速看到市场热点；
- 可以看到资金流入最多的板块和个股；
- 可以辅助判断市场主线。

当前实现状态（2026-07-03）：

- 已实现每日复盘 API：`GET /api/rankings/daily-review`；
- 已实现 Dashboard「每日复盘与排行榜」面板；
- 已支持个股涨幅榜、跌幅榜、成交额榜、换手率榜、主力净流入榜、主力净流出榜；
- 已支持板块涨幅榜、板块资金流榜，数据优先来自同花顺行业摘要（AKShare）；
- 个股行情榜优先使用东方财富轻量直连排行，失败时回退到同花顺网页排行；
- 个股主力资金流榜优先使用东方财富轻量资金流排行，失败时回退到同花顺资金流页面；
- 复盘面板明确标注排行榜仅用于观察市场强弱和资金方向，不构成交易建议。

---

## Phase 7：增强功能

目标：在核心功能稳定后逐步增强。

可选任务：

- 龙虎榜；
- 北向资金；
- 新闻；
- 财务数据；
- AI 个股总结；
- AI 每日复盘；
- 条件预警；
- 自定义指标；
- 多周期共振；
- 本地回测。

注意：即使增加本地回测，也仍然不接自动交易功能。

当前实现状态（2026-07-06）：

- 已实现复盘排行榜点击工作流增强；
- 个股排行榜条目可点击进入个股详情页；
- 板块排行榜条目可点击进入板块详情页；
- 从板块详情中的成分股仍可继续进入个股详情；
- 该阶段只增强复盘导航，不增加交易、预警、回测或 AI 功能。

---

## 9. 推荐目录结构

```text
market-watch-platform/
  README.md
  requirements.txt
  docker-compose.yml
  backend/
    app/
      main.py
      config.py
      database.py
      models/
      schemas/
      api/
        stock.py
        index.py
        sector.py
        moneyflow.py
        watchlist.py
        dashboard.py
      collectors/
        stock_basic_collector.py
        kline_collector.py
        moneyflow_collector.py
        sector_collector.py
      indicators/
        ma.py
        macd.py
        kdj.py
        rsi.py
        boll.py
        position_score.py
        top_bottom_zone.py
        moneyflow_signal.py
      services/
        stock_service.py
        sector_service.py
        dashboard_service.py
      repositories/
        stock_repo.py
        kline_repo.py
        moneyflow_repo.py
        watchlist_repo.py
    tests/
  frontend/
    src/
      main.tsx
      App.tsx
      api/
      components/
        KLineChart.tsx
        VolumeChart.tsx
        MoneyFlowChart.tsx
        TopBottomZoneChart.tsx
        SearchBox.tsx
        WatchlistTable.tsx
        SectorTable.tsx
      pages/
        Dashboard.tsx
        StockDetail.tsx
        SectorDetail.tsx
        Watchlist.tsx
        Rankings.tsx
      types/
      utils/
  data/
    market_watch.db
```

---

## 10. API 设计建议

### 10.1 股票搜索

```text
GET /api/stocks/search?keyword=贵州茅台
```

返回：

```json
[
  {
    "code": "600519",
    "name": "贵州茅台",
    "exchange": "SH"
  }
]
```

### 10.2 个股 K 线

```text
GET /api/stocks/600519/kline?period=daily&start=2020-01-01&end=2026-07-02
```

返回：

```json
[
  {
    "date": "2026-07-02",
    "open": 100.0,
    "high": 105.0,
    "low": 99.0,
    "close": 103.0,
    "volume": 123456,
    "amount": 123456789.0
  }
]
```

### 10.3 个股价格位置

```text
GET /api/stocks/600519/position?window=250
```

返回：

```json
{
  "code": "600519",
  "window": 250,
  "position_score": 87.5,
  "zone": "high_watch",
  "label": "高位观察区"
}
```

### 10.4 个股资金流

```text
GET /api/stocks/600519/moneyflow?start=2026-01-01&end=2026-07-02
```

返回：

```json
[
  {
    "date": "2026-07-02",
    "main_net_inflow": 123456789.0,
    "main_net_ratio": 5.6,
    "super_large_net_inflow": 50000000.0,
    "large_net_inflow": 70000000.0
  }
]
```

### 10.5 Dashboard

```text
GET /api/dashboard
```

返回：

```json
{
  "indices": [],
  "top_sectors": [],
  "money_inflow_sectors": [],
  "watchlist_summary": []
}
```

---

## 11. 图表实现建议

### 11.1 K 线图

建议使用 TradingView Lightweight Charts。

需要支持：

- 蜡烛图；
- 均线；
- 成交量；
- 十字光标；
- 缩放；
- 拖动；
- 时间轴对齐。

### 11.2 资金流柱状图

可以使用：

- Lightweight Charts Histogram Series；
- 或 ECharts Bar Chart。

要求：

- 正值向上；
- 负值向下；
- 与 K 线时间轴对齐；
- 鼠标悬停显示净流入金额；
- 支持显示累计资金流线。

### 11.3 顶底区域图

可以使用：

- K 线背景区域；
- 0-100 副图曲线；
- 横向区域带。

建议初期先做副图：

- Y 轴固定 0-100；
- 0-20 为底部区域；
- 80-100 为顶部区域；
- 当前分数用曲线展示。

等后续稳定后，再做 K 线背景染色。

---

## 12. 数据更新策略

### 12.1 MVP 阶段

MVP 阶段可以先手动刷新。

例如：

- 点击按钮更新当前股票数据；
- 点击按钮更新自选股数据；
- 点击按钮更新板块资金流。

这样最简单，也最容易调试。

### 12.2 自动更新阶段

后续可以加入定时任务：

- 交易日前：更新股票列表、板块列表；
- 交易时间内：每 1-5 分钟更新实时行情；
- 收盘后：更新日 K、资金流、排行榜；
- 夜间：补全历史数据和财务数据。

### 12.3 缓存策略

建议：

- 历史 K 线写入数据库；
- 当日行情可以放缓存；
- 资金流每日入库；
- 查询时优先读本地数据库，缺失时再请求外部数据源。

---

## 13. 开发优先级排序

最高优先级：

1. 股票搜索；
2. 日 K 展示；
3. 成交量；
4. 自选股；
5. 顶底区域指标；
6. 个股主力资金流；
7. 板块主力资金流。

中优先级：

1. 板块详情页；
2. 排行榜；
3. 指数页面；
4. 多周期 K 线；
5. MACD / RSI / KDJ / BOLL。

低优先级：

1. 新闻；
2. 财务；
3. 龙虎榜；
4. AI 分析；
5. 复杂预警；
6. 回测。

---

## 14. 风险和解决方案

### 14.1 数据源不稳定

风险：免费接口可能失效、限流或字段变化。

解决方案：

- 对数据源做封装；
- 每类数据保留备用接口；
- 所有数据先写入本地数据库；
- 前端不直接依赖第三方接口字段。

### 14.2 资金流口径不统一

风险：不同平台的主力资金流数据可能不同。

解决方案：

- 明确标注数据来源；
- 不混用不同来源的资金流字段；
- 同一张图只使用同一种口径；
- 后续如果更换数据源，重新标注。

### 14.3 顶底指标误导

风险：低位不等于马上反弹，高位不等于马上下跌。

解决方案：

- 将指标命名为“价格位置”或“风险区域”，不要命名为“买入/卖出”；
- 显示计算逻辑；
- 加入趋势过滤；
- 避免把它当作单一决策依据。

### 14.4 功能膨胀

风险：一开始做太多功能，导致核心功能迟迟不可用。

解决方案：

- 先完成 MVP；
- 每个阶段都有明确验收标准；
- 核心指标优先；
- 新闻、AI、财务等后置。

---

## 15. 最小可行版本定义

真正的 MVP 应该只包含：

1. 后端能获取并保存个股日 K；
2. 前端能展示 K 线和成交量；
3. 支持股票代码/名称搜索；
4. 支持自选股；
5. 支持价格位置分数；
6. 支持顶部/底部区域展示；
7. 支持个股主力资金流柱状图。

只要这 7 点完成，就已经符合项目核心方向。

---

## 16. 建议的第一周开发任务

如果从零开始，第一周建议只做以下内容：

1. 建立项目目录；
2. FastAPI 后端跑通；
3. React 前端跑通；
4. SQLite 数据库跑通；
5. 用 AKShare 获取一只股票的日 K；
6. 把日 K 存入数据库；
7. 前端画出这只股票的 K 线和成交量；
8. 写出第一个价格位置指标；
9. 在图上显示当前价格位置分数。

第一周不建议做：

- AI；
- 新闻；
- 财务；
- 龙虎榜；
- 复杂板块系统；
- 登录系统；
- 自动交易。

---

## 17. 最终建议

本项目最关键的是不要被“通达信 API”“交易平台”“量化系统”这些概念带偏。

真正应该做的是：

> 一个个人自用、以看盘为核心、以价格位置和主力资金为重点的 A 股市场分析平台。

最好的开发路径是：

1. 先用免费数据源跑通 MVP；
2. 先做日 K、自选股、顶底区域、资金流；
3. 等核心功能稳定后，再扩展板块、排行榜、龙虎榜、新闻、AI 分析；
4. 全程不接入下单功能，避免把项目复杂度和合规风险拉高。
