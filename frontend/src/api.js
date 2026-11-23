// "/api" is proxied to http://localhost:8000 by vite.config.js.
// For production, set VITE_API_URL (e.g. https://bank.example.com) and make sure CORS is enabled on the backend.
const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, opts) {
  const r = await fetch(BASE + path, opts);
  const text = await r.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!r.ok) {
    const d = data && data.detail;
    const msg = Array.isArray(d) ? d.map(x => `${(x.loc || []).slice(1).join(".")}: ${x.msg}`).join("\n") : d || text;
    throw new Error(`Server returned ${r.status}\n${msg}`);
  }
  return data;
}

export const health = () => request("/health");
export const predict = body =>
  request("/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
export const auditLogs = () => request("/audit-logs");
