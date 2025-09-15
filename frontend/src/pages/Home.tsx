import React from "react";

export default function Home(): JSX.Element {
  return (
    <div>
      <div className="card">
        <h1>Welcome to Monexa</h1>
        <p>Your money, simplified — with voice, AI, and insights.</p>
      </div>

      <div className="card">
        <h3>Quick Start</h3>
        <ul>
          <li>Import CSVs from banks, wallets and marketplaces (Import page).</li>
          <li>Open Dashboard for monthly trends.</li>
          <li>Use Chat to ask voice/typed queries like “How much I spent on coffee this month?”.</li>
        </ul>
      </div>
    </div>
  );
}
