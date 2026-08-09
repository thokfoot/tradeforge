"use client";

import { useEffect, useState } from "react";
import Admin from "@/components/Admin";
import AgentBar from "@/components/AgentBar";
import Alerts from "@/components/Alerts";
import Auth from "@/components/Auth";
import Builder from "@/components/Builder";
import Dashboard from "@/components/Dashboard";
import Education from "@/components/Education";
import Journal from "@/components/Journal";
import Onboarding from "@/components/Onboarding";
import Paper from "@/components/Paper";
import Screener from "@/components/Screener";
import Watchlist from "@/components/Watchlist";
import type { User, Market } from "@/lib/api";
import { I18nProvider, useT, useLang } from "@/lib/i18n";

type Tab = "dashboard" | "builder" | "screener" | "paper" | "journal" | "alerts" | "learn" | "watchlist" | "admin";

interface NavItem { id: Tab; icon: string; label: string; section?: string }

function NavGlyph({ id }: { id: Tab }) {
  const props = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  switch (id) {
    case "dashboard": return <svg {...props}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>;
    case "screener": return <svg {...props}><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>;
    case "paper": return <svg {...props}><rect x="3" y="6" width="18" height="14" rx="2" /><path d="M8 6V4h8v2M3 11h18M16 15h2" /></svg>;
    case "builder": return <svg {...props}><rect x="3" y="3" width="6" height="6" rx="1" /><rect x="15" y="15" width="6" height="6" rx="1" /><path d="M9 6h3a3 3 0 0 1 3 3v6M12 18H9a3 3 0 0 1-3-3v-3" /></svg>;
    case "alerts": return <svg {...props}><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>;
    case "journal": return <svg {...props}><path d="M6 3h11a2 2 0 0 1 2 2v16H6a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3Z" /><path d="M6 3v15a3 3 0 0 0 3 3M9 8h6M9 12h6" /></svg>;
    case "watchlist": return <svg {...props}><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z" /></svg>;
    case "learn": return <svg {...props}><path d="m3 8 9-4 9 4-9 4-9-4Z" /><path d="M7 10v5c2.8 2.2 7.2 2.2 10 0v-5M21 8v7" /></svg>;
    case "admin": return <svg {...props}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.1h-2.6v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1A1.7 1.7 0 0 0 8 15a1.7 1.7 0 0 0-1.5-1H6v-2.6h.1A1.7 1.7 0 0 0 8 10a1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V5h2.6v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.5 1h.1v2.6h-.1a1.7 1.7 0 0 0-1.5 1.4Z" /></svg>;
  }
}

function TabContent({ tab, token, user, setTab, setMarket, setSymbol }: {
  tab: Tab; token: string | null; user: User | null;
  setTab: (t: Tab) => void; setMarket: (m: Market) => void; setSymbol: (s: string) => void;
}) {
  switch (tab) {
    case "dashboard": return <Dashboard token={token} user={user} onNavigate={(nextTab) => setTab(nextTab)} />;
    case "builder": return <Builder token={token} user={user} />;
    case "screener": return <Screener token={token} user={user} />;
    case "paper": return <Paper token={token} user={user} />;
    case "journal": return <Journal token={token} user={user} />;
    case "alerts": return <Alerts token={token} user={user} />;
    case "learn": return <Education />;
    case "watchlist": return <Watchlist token={token} user={user} onPick={(m, s) => { setMarket(m); setSymbol(s); setTab("dashboard"); }} />;
    case "admin": return <Admin />;
  }
}

function App() {
  const t = useT();
  const { lang, setLang } = useLang();
  const [tab, setTab] = useState<Tab>("dashboard");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [, setNavMarket] = useState<Market>("IN");
  const [, setNavSymbol] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("tf_token");
    if (saved) { setToken(saved); try { setUser(JSON.parse(localStorage.getItem("tf_user") ?? "null")); } catch { setUser(null); } }
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
      if (event.key === "Escape") setCommandOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function onAuth(tok: string, u: User) { setToken(tok); setUser(u); localStorage.setItem("tf_token", tok); localStorage.setItem("tf_user", JSON.stringify(u)); }
  function onLogout() { setToken(null); setUser(null); localStorage.removeItem("tf_token"); localStorage.removeItem("tf_user"); }

  const nav: NavItem[] = [
    { id: "dashboard", icon: "\u25A0", label: t("tab.charts") },
    { id: "screener", icon: "\u25CB", label: t("tab.screener") },
    { id: "paper", icon: "\u25C6", label: t("tab.paper") },
    { id: "builder", icon: "\u25B3", label: t("tab.builder"), section: "Tools" },
    { id: "alerts", icon: "\u25C9", label: t("tab.alerts") },
    { id: "journal", icon: "\u25A1", label: t("tab.journal") },
    { id: "watchlist", icon: "\u2606", label: t("tab.watchlist"), section: "More" },
    { id: "learn", icon: "\u25CC", label: t("tab.learn") },
  ];
  if (user?.email === "admin@tradeforge.in") nav.push({ id: "admin", icon: "\u2699", label: "Admin", section: "More" });
  const commandItems = nav.filter((item) => item.label.toLowerCase().includes(commandQuery.toLowerCase()));

  return (
    <div className="app-layout">
      <Onboarding />
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon"><span>TF</span></div>
          <div>
            <div className="sidebar-brand-text">Trade Forge</div>
            <div className="sidebar-brand-sub">MARKET LAB / PAPER MODE</div>
          </div>
        </div>

        {nav.map((item, i) => {
          const prev = i > 0 ? nav[i - 1] : null;
          const showDivider = item.section && (!prev || prev.section !== item.section);
          return (
            <div key={item.id}>
              {showDivider && <div className="sidebar-divider">{item.section}</div>}
              <button className={`nav-item ${tab === item.id ? "active" : ""}`} onClick={() => setTab(item.id)} aria-current={tab === item.id ? "page" : undefined}>
                <span className="nav-icon"><NavGlyph id={item.id} /></span> {item.label}
              </button>
            </div>
          );
        })}

        <div className="sidebar-bottom">
          <div className="lang-switch">
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
            <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>HI</button>
          </div>
          <div className="auth-sidebar">
            <Auth user={user} token={token} onAuth={onAuth} onLogout={onLogout} />
          </div>
        </div>
      </aside>

      <div className="mobile-topbar">
        <div className="mobile-brand"><span className="mobile-brand-mark">TF</span><span>Trade Forge</span></div>
        <div className="mobile-live"><span className="dot" /> PAPER MODE</div>
      </div>

      <main className="main-content">
        <div className="topbar">
          <div className="topbar-copy">
            <h1 className="page-title">{nav.find((n) => n.id === tab)?.label ?? ""}</h1>
          </div>
          <div className="topbar-actions">
            <button className="ai-trigger" type="button" onClick={() => window.dispatchEvent(new CustomEvent("tf:ai-toggle"))}><span className="ai-trigger-mark">AI</span><em>Assistant</em></button>
            <button className="command-hint" type="button" onClick={() => { setCommandOpen(true); setCommandQuery(""); }}><span>⌘</span> K <em>Quick search</em></button>
            {tab === "paper" && token && (
              <button className="topbar-paper-reset" type="button" onClick={() => window.dispatchEvent(new CustomEvent("tf:paper-reset"))} disabled={!token}>Reset paper</button>
            )}
            <div className="status-pill"><span className="dot" />3 markets · paper mode</div>
          </div>
        </div>
        <TabContent tab={tab} token={token} user={user} setTab={setTab} setMarket={setNavMarket} setSymbol={setNavSymbol} />
        <footer className="disclaimer">{t("disclaimer")}</footer>
      </main>

      <AgentBar token={token} user={user} onNavigate={(tab) => setTab(tab as Tab)} />

      {commandOpen && (
        <div className="command-backdrop" onMouseDown={() => setCommandOpen(false)}>
          <div className="command-panel" onMouseDown={(event) => event.stopPropagation()}>
            <div className="command-input-wrap">
              <span className="command-search-icon">/</span>
              <input autoFocus value={commandQuery} onChange={(event) => setCommandQuery(event.target.value)} placeholder="Jump to a workspace..." />
              <kbd>ESC</kbd>
            </div>
            <div className="command-label">WORKSPACES</div>
            <div className="command-list">
              {commandItems.map((item) => (
                <button key={item.id} type="button" className={`command-item ${tab === item.id ? "active" : ""}`} onClick={() => { setTab(item.id); setCommandOpen(false); setCommandQuery(""); }}>
                  <span className="command-item-icon"><NavGlyph id={item.id} /></span>
                  <span>{item.label}</span>
                  {tab === item.id && <span className="command-current">CURRENT</span>}
                </button>
              ))}
              {commandItems.length === 0 && <div className="command-empty">No workspace matches that search.</div>}
            </div>
            <div className="command-footer"><span><kbd>↑↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span></div>
          </div>
        </div>
      )}

      <nav className="mobile-nav" aria-label="Mobile navigation">
        {nav.map((item) => (
          <button key={item.id} className={`mobile-nav-item ${tab === item.id ? "active" : ""}`} onClick={() => setTab(item.id)} aria-current={tab === item.id ? "page" : undefined}>
            <span className="mobile-nav-icon"><NavGlyph id={item.id} /></span>
            <span>{item.label.replace(" + Backtest", "").replace(" Trading", "")}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

export default function Home() { return <I18nProvider><App /></I18nProvider>; }
