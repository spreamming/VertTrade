# Stage 14 数据源策略说明

VertTrade 使用多个免费数据源，**不同页面/字段可能来自不同 provider**。这是有意为之：在稳定性与字段可用性之间做 trade-off。

## 原则

1. **排行榜统一同花顺（THS）**：避免同一榜单在不同刷新间切换 universe 或排序语义。
2. **个股/板块资金流统一东方财富（EM）**：字段较完整，含超大/大/中/小单拆分（个股）。
3. **日 K 优先 AKShare/EM，失败 fallback 腾讯**：保证历史 K 线可恢复。
4. **近实时行情腾讯优先，EM fallback**：带 quote time 与 stale 标记。
5. **板块列表 EM 优先，THS fallback**；**板块 K 线 THS 优先，EM fallback**。
6. **市场概览指数腾讯，涨跌家数乐股网（Legu）**：仅作观察参考。

## 按功能的数据源

| 功能 | 主数据源 | Fallback | 备注 |
|------|----------|----------|------|
| 股票搜索 / 基础信息 | AKShare 股票列表 | — | SQLite 缓存 |
| 日 K 线 | AKShare EM | 腾讯 | SQLite 持久化；4 日 end 容忍 |
| 分钟 K | 新浪（AKShare） | 东方财富 | 20s 内存缓存 |
| 分时图 | 腾讯 | 东方财富 | 15s 内存缓存 |
| 近实时报价 | 腾讯 | 东方财富 | 3s 内存缓存 + 同代码锁 |
| 个股资金流 | 东方财富 | 同花顺快照（仅汇总） | SQLite 持久化 |
| 价格位置 | 本地计算 | — | 基于日 K |
| 行业板块列表 | 东方财富 | 同花顺 | 60s 内存缓存 |
| 板块成分股 | 东方财富 | 同花顺 | 300s 内存缓存 |
| 板块 K 线 | 同花顺 | 东方财富 | 60s 内存缓存 + stale fallback |
| 板块资金流 | 东方财富 | — | 60s 内存缓存 + stale fallback |
| 排行榜（8 组） | 同花顺 | 无（THS-only） | 60s 全成功才缓存 |
| 市场指数 | 腾讯 | stale 上次缓存 | 10s 内存缓存 |
| 涨跌家数 | 乐股网 | 可缺失 | 不影响指数展示 |

## 已知「混用」场景

- **Dashboard 板块主力净流入（THS 板块列表）** vs **板块详情资金流图（EM）**：数值口径可能不一致，UI 已标注来源。
- **排行榜板块资金流（THS）** vs **板块详情 EM 资金流**：仅作方向观察，不宜逐元对比。
- **THS 个股资金流 fallback**：无分单明细，资金流视角切换会禁用非主力选项。

## 并发与稳定性

- `THS_PROVIDER_LOCK`：序列化同花顺/py_mini_racer 调用，防止并发崩溃。
- 个股 live quote / 日 K / 资金流：按代码 in-flight 锁，减少 cache penetration。
- 板块/排行榜/市场概览：短 TTL 内存缓存 + stale-while-revalidate。

## 收盘后数据更新

- **无后台定时任务**。日 K / 资金流在 end date 落后超过 4 个自然日时会自动触发拉取。
- 可手动运行：` .venv/bin/python scripts/refresh_watchlist_cache.py`

## 非交易边界

本项目不包含券商 API、下单、自动交易或账户凭证存储。详见 `market_watch_requirements.md`。
