"use client";

import { useState } from "react";
import { login, register, subscribe, type User } from "@/lib/api";

export default function Auth({
  user,
  token,
  onAuth,
  onLogout,
}: {
  user: User | null;
  token: string | null;
  onAuth: (token: string, user: User) => void;
  onLogout: () => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const res = mode === "login" ? await login(email, password) : await register(email, password);
      onAuth(res.token, res.user);
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  async function onUpgrade() {
    setError("");
    try {
      if (!token) return;
      const updated = await subscribe("pro", token);
      onAuth(token, updated);
    } catch (err) {
      setError(String((err as Error).message ?? err));
    }
  }

  if (user) {
    return (
      <div className="auth-box">
        <span className="muted">
          {user.email} · <b className={user.plan === "pro" ? "pro" : "free"}>{user.plan}</b>
        </span>
        {user.plan === "free" && (
          <button className="small" onClick={onUpgrade}>
            Upgrade to Pro ₹199/mo
          </button>
        )}
        <button className="small ghost" onClick={onLogout}>
          Logout
        </button>
      </div>
    );
  }

  return (
    <form className="auth-box" onSubmit={onSubmit}>
      <div className="auth-row">
        <input
          placeholder="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          placeholder="password (min 8)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="small" type="submit">
          {mode === "login" ? "Login" : "Register"}
        </button>
        <button
          className="small ghost"
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Register" : "Login"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
