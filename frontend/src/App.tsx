import { useState } from "react";

import { type StockSummary } from "./api/client";
import { SearchBox } from "./components/SearchBox";
import { StockDetail } from "./pages/StockDetail";
import "./styles.css";

function App() {
  const [selectedStock, setSelectedStock] = useState<StockSummary | null>(null);

  if (selectedStock) {
    return (
      <StockDetail
        stock={selectedStock}
        onBack={() => setSelectedStock(null)}
      />
    );
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">个人 A 股看盘工具</p>
        <h1>VertTrade</h1>
        <p>
          搜索 A 股代码或名称，查看日 K 线、成交量和最新行情摘要。
        </p>
      </section>

      <SearchBox onSelect={setSelectedStock} />

      <section className="status-card">
        <h2>第一阶段功能</h2>
        <ul className="stage-list">
          <li>支持按股票代码或名称搜索。</li>
          <li>打开个股详情页，查看最新行情摘要。</li>
          <li>查看日 K 线和成交量，支持缩放、拖动和十字光标。</li>
          <li>拉取到的 K 线数据会缓存到本地 SQLite。</li>
        </ul>
      </section>
    </main>
  );
}

export default App;
