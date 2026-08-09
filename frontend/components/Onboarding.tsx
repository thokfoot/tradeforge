"use client";

import { useEffect, useState } from "react";
import { useT, useLang } from "@/lib/i18n";

export default function Onboarding() {
  const t = useT();
  const { setLang } = useLang();
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("tf_onboarding_done")) setVisible(true);
  }, []);

  function finish() { localStorage.setItem("tf_onboarding_done", "1"); setVisible(false); }

  if (!visible) return null;

  const steps = [
    { emoji: "\u{1F44B}", title: t("onboarding.welcome"), body: "Trade Forge ek complete paper trading aur backtesting platform hai. India, US aur Crypto markets ke liye. Bina kisi risk ke seekho aur practice karo — bilkul free." },
    { emoji: "\u{1F4C8}", title: t("onboarding.step1"), body: "Dashboard mein market (IN/US/CRYPTO) aur koi bhi symbol select karo. Real candlestick chart aur backtest turant dikhega." },
    { emoji: "\u2699\uFE0F", title: t("onboarding.step2"), body: "Strategy Builder mein bina coding ke entry/exit rules banao. Ya code khud likho. Run Backtest dabao — real Indian brokerage costs ke saath result." },
    { emoji: "\u{1F4B0}", title: t("onboarding.step3"), body: "Paper Trading mein virtual \u20B91,00,000 ke saath practice karo. Market orders, positions, P&L — sab real prices pe simulate hota hai." },
    { emoji: "\u2705", title: t("onboarding.done"), body: "Ab aap taiyar hain. Screener, Alerts, Journal aur AI assistant explore karo. EN/HI toggle se Hindi mein switch karo. Happy trading!" },
  ];

  const s = steps[step];
  const last = step === steps.length - 1;

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-dialog">
        <div className="onboarding-emoji">{s.emoji}</div>
        <h2>{s.title}</h2>
        <p>{s.body}</p>
        <div className="onboarding-footer">
          <div className="lang-switch">
            <button onClick={() => setLang("en")}>EN</button>
            <button onClick={() => setLang("hi")}>HI</button>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <div className="onboarding-dots">
              {steps.map((_, i) => <div key={i} className={`ob-dot ${i === step ? "on" : ""}`} />)}
            </div>
            {step > 0 && <button className="btn-secondary btn-sm" onClick={() => setStep(step - 1)}>Back</button>}
            {last ? <button className="btn-primary btn-sm" onClick={finish}>Let&apos;s Go</button>
             : <button className="btn-primary btn-sm" onClick={() => setStep(step + 1)}>Next</button>}
          </div>
        </div>
      </div>
    </div>
  );
}
