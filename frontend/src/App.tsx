import { useState } from "react";

import { type StockSummary } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
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

  return <Dashboard onOpenStock={setSelectedStock} />;
}

export default App;
