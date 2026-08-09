// Trade Forge AI Agent — Layer 1 "listener" (Cloudflare Workers AI).
//
// Deploy:
//   npx wrangler deploy scripts/cloudflare_parser_worker.js --name tf-agent-parser
//   # Add binding via wrangler.toml or dashboard: AI = Workers AI
//   # Then set CLOUDFLARE_AI_URL=<worker-url> and CLOUDFLARE_AI_TOKEN=<API token>
//   # in the backend .env (see .env.example).
//
// Input:  POST { "text": "RELIANCE RSI 30 se neeche aaye toh buy, SL 1%, TP 2%" }
// Output: { "dsl": { "intent": "run_backtest", "symbol": "RELIANCE",
//                   "entry": { "indicator": "RSI", "op": "below", "value": 30 },
//                   "sl": 1, "tp": 2 } }
//
// The backend validates the returned DSL and falls back to its local
// heuristic parser if anything is malformed.

const SYSTEM = [
  "You are Trade Forge DSL parser. Convert Hindi/English to JSON only.",
  'Schema: {"intent":"create_strategy|run_backtest|review","symbol":string,',
  '"entry":{"indicator":"RSI|MA|EMA|SUPERTREND","op":"below|above","value":number},',
  '"sl":number,"tp":number}',
  'Rules: sl/tp are percentages (1 means 1%). op is "below" or "above" only.',
  'If user says "review" set intent=review and skip entry/sl/tp. Output JSON only, no explanation.',
].join("\n");

function extractJson(raw) {
  const text = String(raw ?? "");
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) return null;
  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
}

function normalize(dsl) {
  if (!dsl || typeof dsl !== "object") return null;
  const out = {};
  if (typeof dsl.intent === "string" && dsl.intent) out.intent = dsl.intent;
  if (typeof dsl.symbol === "string" && dsl.symbol.trim()) out.symbol = dsl.symbol.trim().toUpperCase();
  const entry = dsl.entry && typeof dsl.entry === "object" ? dsl.entry : {};
  if (entry.indicator && entry.value !== undefined && entry.value !== null) {
    out.entry = {
      indicator: String(entry.indicator).toUpperCase(),
      op: String(entry.op ?? "below").toLowerCase() === "above" ? "above" : "below",
      value: Number(entry.value),
    };
  }
  for (const key of ["sl", "tp"]) {
    if (dsl[key] !== undefined && dsl[key] !== null) {
      const n = Number(dsl[key]);
      if (Number.isFinite(n)) out[key] = n;
    }
  }
  return Object.keys(out).length ? out : null;
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return json({ error: "POST only" }, 405);
    }
    if (!env.AI) {
      return json({ error: "Workers AI binding 'AI' not configured" }, 500);
    }
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid json body" }, 400);
    }
    const text = String(body?.text ?? "").slice(0, 500);
    if (!text) {
      return json({ error: "text required" }, 400);
    }
    try {
      const resp = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
        messages: [
          { role: "system", content: SYSTEM },
          { role: "user", content: `Text: ${text}\nOutput JSON:` },
        ],
        temperature: 0.1,
        max_tokens: 250,
      });
      const dsl = normalize(extractJson(resp?.response ?? resp));
      if (!dsl) {
        return json({ error: "could not parse DSL from model output" }, 502);
      }
      return json({ dsl });
    } catch (e) {
      return json({ error: String(e?.message ?? e) }, 502);
    }
  },
};

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}
