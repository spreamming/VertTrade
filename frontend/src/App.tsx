import { useState } from "react";

import { type SectorSummary, type StockSummary } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
import { SectorDetail } from "./pages/SectorDetail";
import { StockDetail } from "./pages/StockDetail";
import "./styles.css";

function App() {
  const [selectedStock, setSelectedStock] = useState<StockSummary | null>(null);
  const [selectedSector, setSelectedSector] = useState<SectorSummary | null>(null);

  if (selectedStock) {
    return (
      <StockDetail
        stock={selectedStock}
        onBack={() => setSelectedStock(null)}
      />
    );
  }

  if (selectedSector) {
    return (
      <SectorDetail
        sector={selectedSector}
        onBack={() => setSelectedSector(null)}
        onOpenStock={setSelectedStock}
      />
    );
  }

  return (
    <Dashboard
      onOpenStock={setSelectedStock}
      onOpenSector={setSelectedSector}
    />
  );
}

export default App;
