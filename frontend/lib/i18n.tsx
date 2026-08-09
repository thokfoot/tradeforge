"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useState } from "react";

export type Lang = "en" | "hi";

const translations: Record<string, Record<Lang, string>> = {
  "app.title": { en: "Trade Forge", hi: "Trade Forge" },
  "app.tag": { en: "paper trading + backtesting + screener + journal", hi: "paper trading + backtesting + screener + journal" },
  "tab.charts": { en: "Charts + Backtest", hi: "Charts + Backtest" },
  "tab.builder": { en: "Strategy Builder", hi: "Strategy Builder" },
  "tab.screener": { en: "Screener", hi: "Screener" },
  "tab.paper": { en: "Paper Trading", hi: "Paper Trading" },
  "tab.journal": { en: "Journal", hi: "Journal" },
  "tab.alerts": { en: "Alerts", hi: "Alerts" },
  "tab.learn": { en: "Learn", hi: "Sikho" },
  "tab.watchlist": { en: "Watchlist", hi: "Watchlist" },
  "login.title": { en: "Login", hi: "Login" },
  "login.email": { en: "Email", hi: "Email" },
  "login.password": { en: "Password", hi: "Password" },
  "login.button": { en: "Login", hi: "Login" },
  "login.register": { en: "Register", hi: "Register" },
  "login.logout": { en: "Logout", hi: "Logout" },
  "login.welcome": { en: "Welcome,", hi: "Swagat hai," },
  "login.required": { en: "Login to access Pro features.", hi: "Pro features ke liye login karo." },
  "auth.plan": { en: "Plan:", hi: "Plan:" },
  "auth.subscribe": { en: "Go Pro", hi: "Pro bano" },
  "auth.needLogin": { en: "Login required", hi: "Login karo" },
  "paper.title": { en: "Paper Trading", hi: "Paper Trading" },
  "paper.balance": { en: "Balance", hi: "Balance" },
  "paper.equity": { en: "Equity", hi: "Equity" },
  "paper.positions": { en: "Positions", hi: "Positions" },
  "paper.history": { en: "Trade History", hi: "Trade History" },
  "paper.buy": { en: "Buy", hi: "Kharido" },
  "paper.sell": { en: "Sell", hi: "Becho" },
  "paper.qty": { en: "Qty", hi: "Qty" },
  "paper.reset": { en: "Reset Account", hi: "Account Reset" },
  "paper.login": { en: "Paper trading ke liye login karo.", hi: "Paper trading ke liye login karo." },
  "screener.title": { en: "Screener", hi: "Screener" },
  "screener.scan": { en: "Scan", hi: "Scan" },
  "screener.filters": { en: "Filters", hi: "Filters" },
  "screener.results": { en: "Results", hi: "Results" },
  "screener.save": { en: "Save Scan", hi: "Scan Save" },
  "screener.login": { en: "Scan save karne ke liye login karo.", hi: "Scan save karne ke liye login karo." },
  "journal.title": { en: "Trading Journal", hi: "Trading Journal" },
  "journal.add": { en: "Add Entry", hi: "Entry Jodo" },
  "journal.note": { en: "Note", hi: "Note" },
  "journal.rating": { en: "Rating (1-5)", hi: "Rating (1-5)" },
  "journal.lesson": { en: "Lesson learned", hi: "Kya seekha" },
  "journal.login": { en: "Journal ke liye login karo.", hi: "Journal ke liye login karo." },
  "alerts.title": { en: "Alerts", hi: "Alerts" },
  "alerts.add": { en: "Add Alert", hi: "Alert Jodo" },
  "alerts.check": { en: "Check now", hi: "Abhi check karo" },
  "alerts.login": { en: "Alerts ke liye login karo.", hi: "Alerts ke liye login karo." },
  "builder.title": { en: "Strategy Builder", hi: "Strategy Builder" },
  "builder.generate": { en: "Generate Strategy", hi: "Strategy banao" },
  "builder.backtest": { en: "Run Backtest", hi: "Backtest chalao" },
  "dashboard.title": { en: "Charts + Backtest", hi: "Charts + Backtest" },
  "dashboard.run": { en: "Run Backtest", hi: "Backtest chalao" },
  "dashboard.replay": { en: "Replay to Paper", hi: "Paper mein replay" },
  "dashboard.symbol": { en: "Symbol", hi: "Symbol" },
  "dashboard.market": { en: "Market", hi: "Market" },
  "dashboard.interval": { en: "Interval", hi: "Interval" },
  "learn.title": { en: "Learning Center", hi: "Learning Center" },
  "admin.title": { en: "Admin Dashboard", hi: "Admin" },
  "onboarding.welcome": { en: "Welcome to Trade Forge!", hi: "Trade Forge mein swagat hai!" },
  "onboarding.step1": { en: "Step 1: Pick a market and symbol to see real charts.", hi: "Step 1: Market aur symbol chuno real charts dekhne ke liye." },
  "onboarding.step2": { en: "Step 2: Run a backtest with a sample strategy.", hi: "Step 2: Sample strategy ke saath backtest chalao." },
  "onboarding.step3": { en: "Step 3: Try paper trading with virtual money.", hi: "Step 3: Virtual paise se paper trading try karo." },
  "onboarding.done": { en: "You're all set! Explore the tabs above.", hi: "Taiyar ho! Upar tabs explore karo." },
  "common.loading": { en: "Loading...", hi: "Load ho raha hai..." },
  "common.error": { en: "Error", hi: "Galti" },
  "common.save": { en: "Save", hi: "Save" },
  "common.delete": { en: "Delete", hi: "Delete" },
  "common.cancel": { en: "Cancel", hi: "Cancel" },
  "common.yes": { en: "Yes", hi: "Haan" },
  "common.no": { en: "No", hi: "Nahi" },
  "disclaimer": { en: "Educational use only. Past performance does not guarantee future results. Paper trading — no real orders.", hi: "Sirf educational use ke liye. Past performance future results ki guarantee nahi. Paper trading — koi real order nahi." },
};

interface I18nContextType {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: "en",
  setLang: () => {},
  t: (k) => translations[k]?.en ?? k,
});

export function useT() {
  const ctx = useContext(I18nContext);
  return ctx.t;
}

export function useLang() {
  const ctx = useContext(I18nContext);
  return { lang: ctx.lang, setLang: ctx.setLang };
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");

  function t(key: string): string {
    return translations[key]?.[lang] ?? key;
  }

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}
