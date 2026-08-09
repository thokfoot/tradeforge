"use client";

import { useEffect, useRef, useState } from "react";
import {
  agentParse,
  agentRun,
  agentReview,
  agentSuggest,
  agentHistory,
  type AgentDsl,
  type AgentMetrics,
  type User,
} from "@/lib/api";

type Message =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "agent"; kind: "text"; text: string }
  | { id: string; role: "agent"; kind: "plan"; dsl: AgentDsl; plan_text: string }
  | { id: string; role: "agent"; kind: "result"; summary: string; metrics: AgentMetrics; chips: string[]; backtestId: string }
  | { id: string; role: "agent"; kind: "review"; text: string; chips: string[] };

const FIXED_CHIPS = ["SL bada karu?", "NIFTY 50 par test karu?", "Journal dekhu?"];

let nextId = 0;
const uid = () => `m${Date.now()}_${nextId++}`;

function fmtPct(v: number | undefined | null): string {
  if (v == null || Number.isNaN(v)) return "–";
  return `${v.toFixed(1)}%`;
}

export default function AgentBar({
  token,
  user,
  onNavigate,
}: {
  token: string | null;
  user: User | null;
  onNavigate: (tab: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onToggle() {
      setOpen((o) => !o);
    }
    window.addEventListener("tf:ai-toggle", onToggle);
    return () => window.removeEventListener("tf:ai-toggle", onToggle);
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, busy]);

  function push(msg: Message) {
    setMessages((prev) => [...prev, msg]);
  }

  async function runPipeline(text: string) {
    if (!token) {
      setError("Login karo pehle — AI Agent ke liye login zaroori hai.");
      return;
    }
    setError("");
    push({ id: uid(), role: "user", text });
    setBusy(true);
    try {
      const parsed = await agentParse(text, token);
      const dsl = parsed.dsl;
      if (dsl.intent === "review") {
        const { records } = await agentHistory(token, 10);
        const match =
          records.find((r) => r.symbol.toUpperCase() === dsl.symbol.toUpperCase()) ?? records[0];
        if (!match) {
          push({
            id: uid(),
            role: "agent",
            kind: "text",
            text: `Koi purana backtest nahi mila ${dsl.symbol} ke liye. Pehle koi strategy chala ke dekh lo, phir main review kar dunga.`,
          });
          return;
        }
        const review = await agentReview(match.id, token);
        push({ id: uid(), role: "agent", kind: "review", text: review.review, chips: review.chips });
        return;
      }
      push({ id: uid(), role: "agent", kind: "plan", dsl, plan_text: parsed.plan_text ?? "" });
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function onRun(dsl: AgentDsl) {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      const result = await agentRun(dsl, token);
      let chips: string[] = [];
      try {
        const suggested = await agentSuggest(result.metrics, token);
        chips = suggested.chips;
      } catch {
        chips = [];
      }
      push({
        id: uid(),
        role: "agent",
        kind: "result",
        summary: result.summary,
        metrics: result.metrics,
        chips,
        backtestId: result.backtest_id,
      });
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function onReviewChip() {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      const { records } = await agentHistory(token, 1);
      if (!records.length) {
        setError("Pehle koi backtest chalao, phir review kar sakta hoon.");
        return;
      }
      const review = await agentReview(records[0].id, token);
      push({ id: uid(), role: "agent", kind: "review", text: review.review, chips: review.chips });
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  }

  function onChip(chip: string) {
    if (chip === "Journal dekhu?") {
      onNavigate("journal");
      setOpen(false);
      return;
    }
    if (chip === "SL bada karu?") {
      setInput("SL bada karke strategy chalao — SL 2% kar do");
      void runPipeline("SL bada karke strategy chalao — SL 2% kar do");
      return;
    }
    if (chip === "NIFTY 50 par test karu?") {
      void runPipeline("NIFTY 50 par same strategy test karo");
      return;
    }
    void runPipeline(chip);
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    void runPipeline(text);
  }

  const m = messages[messages.length - 1];

  return (
    <div className="agent-float">
      {open && (
        <section className="agent-panel" role="dialog" aria-label="AI Agent">
          <header className="agent-header">
            <div className="agent-title">
              <span className="agent-mini">AI</span>
              <div>
                <b>Agent</b>
                <small>Hinglish mein bolo — main plan, test aur review karta hoon</small>
              </div>
            </div>
            <div className="row" style={{ gap: 7 }}>
              {user?.plan === "pro" ? <span className="badge-pro">PRO</span> : <span className="badge-free">FREE</span>}
              <button className="agent-close" type="button" aria-label="Close AI Agent" onClick={() => setOpen(false)}>×</button>
            </div>
          </header>

          <div className="agent-list" ref={listRef}>
            {messages.length === 0 && (
              <p className="agent-empty">
                Try: <em>“RELIANCE RSI 30 se neeche buy, SL 1%, TP 2%”</em> ya <em>“AAPL review karo”</em>
              </p>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`agent-row ${msg.role === "user" ? "user" : "agent"}`}>
                {msg.role === "user" ? (
                  <div className="agent-bubble user">{msg.text}</div>
                ) : msg.kind === "text" ? (
                  <div className="agent-bubble">{msg.text}</div>
                ) : msg.kind === "plan" ? (
                  <div className="agent-bubble">
                    <div className="agent-card-label">PLAN · samajh gaya</div>
                    <p className="agent-plan">{msg.plan_text}</p>
                    <div className="agent-meta">Symbol: {msg.dsl.symbol} · Entry: {msg.dsl.entry?.indicator}{msg.dsl.entry?.op}{msg.dsl.entry?.value}</div>
                    <div className="agent-chip-row">
                      <button className="btn-primary btn-sm" onClick={() => onRun(msg.dsl)} disabled={busy}>
                        ▶ Chalao
                      </button>
                      <button className="btn-sm ghost" onClick={() => setMessages((prev) => prev.filter((x) => x.id !== msg.id))}>✕</button>
                    </div>
                  </div>
                ) : msg.kind === "result" ? (
                  <div className="agent-bubble">
                    <div className="agent-card-label">RESULT · backtest ho gaya</div>
                    <p className="agent-summary">{msg.summary}</p>
                    <div className="agent-metrics">
                      <div className="agent-metric"><span>Return</span><b className={msg.metrics.total_return_pct >= 0 ? "text-up" : "text-down"}>{fmtPct(msg.metrics.total_return_pct)}</b></div>
                      <div className="agent-metric"><span>Win</span><b>{fmtPct(msg.metrics.win_rate_pct)}</b></div>
                      <div className="agent-metric"><span>Max DD</span><b className="text-down">{fmtPct(msg.metrics.max_drawdown_pct)}</b></div>
                      <div className="agent-metric"><span>Trades</span><b>{msg.metrics.total_trades}</b></div>
                      <div className="agent-metric"><span>Sharpe</span><b>{msg.metrics.sharpe != null ? msg.metrics.sharpe.toFixed(2) : "–"}</b></div>
                      <div className="agent-metric"><span>PF</span><b>{msg.metrics.profit_factor != null ? msg.metrics.profit_factor.toFixed(2) : "–"}</b></div>
                    </div>
                    {(msg.chips.length > 0 || FIXED_CHIPS.length > 0) && (
                      <div className="agent-chip-row">
                        {[...msg.chips, ...FIXED_CHIPS].slice(0, 4).map((chip) => (
                          <button key={chip} type="button" className="chip" onClick={() => onChip(chip)} disabled={busy}>{chip}</button>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="agent-bubble">
                    <div className="agent-card-label">REVIEW · agent ka brain</div>
                    <p className="agent-review">{msg.text}</p>
                    {msg.chips.length > 0 && (
                      <div className="agent-chip-row">
                        {msg.chips.map((chip) => (
                          <button key={chip} type="button" className="chip" onClick={() => onChip(chip)} disabled={busy}>{chip}</button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {busy && (
              <div className="agent-row agent">
                <div className="agent-bubble agent-typing"><span /><span /><span /></div>
              </div>
            )}
          </div>

          {error && <p className="error-msg agent-error">{error}</p>}
          {!token && <p className="text-muted text-sm agent-login-note">Login required for the AI Agent.</p>}

          <div className="agent-chip-row agent-quickchips">
            {FIXED_CHIPS.map((chip) => (
              <button key={chip} type="button" className="chip" onClick={() => onChip(chip)} disabled={busy}>
                {chip}
              </button>
            ))}
          </div>

          <form className="agent-composer" onSubmit={onSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Strategy bolo... (RSI 30 buy, SL 1%, TP 2%)"
              disabled={!token || busy}
            />
            <button className="btn-primary btn-sm" type="submit" disabled={!token || !input.trim() || busy}>
              Send
            </button>
          </form>
          {m?.role === "agent" && m.kind === "result" && (
            <button className="agent-review-btn" type="button" onClick={onReviewChip} disabled={busy}>
              💡 Is backtest ka AI review le lo
            </button>
          )}
        </section>
      )}
    </div>
  );
}
