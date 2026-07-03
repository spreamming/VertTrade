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
        <h2>Stage 0 Readiness</h2>
        {health ? (
          <dl className="status-grid">
            <div>
              <dt>API</dt>
              <dd>{health.status}</dd>
            </div>
            <div>
              <dt>SQLite</dt>
              <dd>{health.database}</dd>
            </div>
            <div>
              <dt>Environment</dt>
              <dd>{health.environment}</dd>
            </div>
          </dl>
        ) : (
          <p>{error ?? "Checking backend..."}</p>
        )}
      </section>

      <section className="status-card">
        <h2>Foundation Scope</h2>
        <ul className="stage-list">
          <li>FastAPI backend with CORS enabled for local Vite.</li>
          <li>React + TypeScript frontend connected to the health endpoint.</li>
          <li>SQLite database file initialized under local project data.</li>
          <li>Next: fetch and cache the first daily K-line dataset.</li>
        </ul>
      </section>
    </main>
  );
}

export default App;
