"use client";

import { useState } from "react";
import { login, register, subscribe, type User } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function Auth({ user, token, onAuth, onLogout }: {
  user: User | null; token: string | null;
  onAuth: (t: string, u: User) => void; onLogout: () => void;
}) {
  const t = useT();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [show, setShow] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError("");
    try {
      const res = mode === "login" ? await login(email, password) : await register(email, password);
      onAuth(res.token, res.user); setShow(false);
    } catch (err) { setError(String((err as Error).message ?? err)); }
  }

  async function upgrade() {
    if (!token) return;
    try { const u = await subscribe("pro", token); onAuth(token, u); } catch (err) { setError(String((err as Error).message ?? err)); }
  }

  if (user) {
    return (
      <div>
        <div style={{ fontSize: 11, color: "var(--text2)", marginBottom: 4, wordBreak: "break-all" }}>{user.email}</div>
        <div className="row" style={{ gap: 6 }}>
          {user.plan === "pro" ? <span className="badge-pro">PRO</span> : <span className="badge-free">FREE</span>}
          {user.plan === "free" && <button className="btn-primary btn-xs" onClick={upgrade}>Upgrade</button>}
          <button className="btn-secondary btn-xs" onClick={onLogout}>Logout</button>
        </div>
      </div>
    );
  }

  if (!show) return <button className="btn-secondary btn-sm" onClick={() => setShow(true)} style={{ width: "100%" }}>{t("login.button")}</button>;

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <input placeholder="email@example.com" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ fontSize: 12, padding: "7px 10px" }} />
      <input placeholder="password (8+ chars)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ fontSize: 12, padding: "7px 10px" }} />
      <div className="row" style={{ gap: 4 }}>
        <button className="btn-primary btn-sm" type="submit" style={{ flex: 1 }}>{mode === "login" ? "Login" : "Register"}</button>
        <button className="btn-secondary btn-sm" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>Switch</button>
      </div>
      {error && <div className="error-msg" style={{ fontSize: 11 }}>{error}</div>}
    </form>
  );
}
