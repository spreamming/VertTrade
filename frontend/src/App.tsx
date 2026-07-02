import { useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "./api/client";
import "./styles.css";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown API error");
      });
  }, []);

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Personal A-share market watch</p>
        <h1>VertTrade</h1>
        <p>
          A private desktop-first market analysis platform for K-lines, price
          position, top/bottom risk zones, money flow, sectors, and watchlists.
        </p>
      </section>

      <section className="status-card">
        <h2>Backend Status</h2>
        {health ? (
          <p>
            {health.app} API is <strong>{health.status}</strong> in{" "}
            {health.environment} mode.
          </p>
        ) : (
          <p>{error ?? "Checking backend..."}</p>
        )}
      </section>
    </main>
  );
}

export default App;
