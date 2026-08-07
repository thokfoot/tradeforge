"use client";

import { useEffect, useState } from "react";
import Alerts from "@/components/Alerts";
import Auth from "@/components/Auth";
import Dashboard from "@/components/Dashboard";
import Journal from "@/components/Journal";
import Paper from "@/components/Paper";
import Screener from "@/components/Screener";
import type { User } from "@/lib/api";

type Tab = "dashboard" | "screener" | "paper" | "journal" | "alerts";

const TABS: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Charts + Backtest" },
  { id: "screener", label: "Screener" },
  { id: "paper", label: "Paper Trading" },
  { id: "journal", label: "Journal" },
  { id: "alerts", label: "Alerts" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("tf_token");
    if (saved) {
      setToken(saved);
      try {
        setUser(JSON.parse(localStorage.getItem("tf_user") ?? "null"));
      } catch {
        setUser(null);
      }
    }
  }, []);

  function onAuth(nextToken: string, nextUser: User) {
    setToken(nextToken);
    setUser(nextUser);
    localStorage.setItem("tf_token", nextToken);
    localStorage.setItem("tf_user", JSON.stringify(nextUser));
  }

  function onLogout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem("tf_token");
    localStorage.removeItem("tf_user");
  }

  return (
    <main className="page">
      <header className="header">
        <h1>⚒️ Trade Forge</h1>
        <span className="tag">paper trading + backtesting + screener + journal</span>
        <Auth user={user} token={token} onAuth={onAuth} onLogout={onLogout} />
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && <Dashboard token={token} user={user} />}
      {tab === "screener" && <Screener token={token} user={user} />}
      {tab === "paper" && <Paper />}
      {tab === "journal" && <Journal token={token} user={user} />}
      {tab === "alerts" && <Alerts token={token} user={user} />}

      <footer className="disclaimer small">
        ⚠️ Educational use only. Past performance does not guarantee future results. Paper trading — no real orders.
      </footer>
    </main>
  );
}
