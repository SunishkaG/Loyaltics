export const inr = n => "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const pretty = k => k.replace(/_/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2");

export function fmtVal(k, v) {
  if (typeof v === "number") {
    if (/inr|revenue|value|saving|cost/i.test(k)) return inr(v);
    if (/prob|rate|reduction|change|delta/i.test(k) && Math.abs(v) <= 1) return (v * 100).toFixed(1) + "%";
    return Number.isInteger(v) ? v : v.toFixed(3);
  }
  if (v && typeof v === "object") return JSON.stringify(v);
  return String(v);
}

// Finds a churn probability anywhere near the top of the response (0–1 or 0–100)
export function findProb(o, depth = 0) {
  if (!o || typeof o !== "object" || Array.isArray(o) || depth > 2) return null;
  for (const [k, v] of Object.entries(o))
    if (typeof v === "number" && /prob|churn|risk_score|score/i.test(k) && !/revenue|inr|cibil/i.test(k)) return { key: k, v };
  for (const v of Object.values(o)) { const f = findProb(v, depth + 1); if (f) return f; }
  return null;
}
