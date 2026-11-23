import { findProb, fmtVal, pretty } from "./util.js";

function Stats({ obj }) {
  return (
    <div className="stats">
      {Object.entries(obj).map(([k, v]) => (
        <div className="stat" key={k}><b>{fmtVal(k, v)}</b><span>{pretty(k)}</span></div>
      ))}
    </div>
  );
}

function Shap({ items }) {
  const max = Math.max(...items.map(s => Math.abs(s.SHAP_Impact))) || 1;
  return (
    <>
      <h3>What drives this score</h3>
      <p className="hint">Bars to the right push churn risk up; bars to the left pull it down.</p>
      {items.map(s => {
        const pos = s.SHAP_Impact >= 0;
        const w = (Math.abs(s.SHAP_Impact) / max) * 50;
        return (
          <div className="shap" key={s.Feature}>
            <span>{pretty(s.Feature)}</span>
            <div className="track">
              <i style={{ [pos ? "left" : "right"]: "50%", width: w + "%", background: pos ? "var(--risk)" : "var(--safe)" }} />
            </div>
            <code>{s.SHAP_Impact.toFixed(2)}</code>
          </div>
        );
      })}
    </>
  );
}

function Interventions({ items }) {
  return (
    <>
      <h3>Retention options</h3>
      <div className="cards">
        {items.map((it, i) => {
          if (it === null || typeof it !== "object") return <div className="card" key={i}>{String(it)}</div>;
          const tk = Object.keys(it).find(k => /name|intervention|action|scenario|title|description/i.test(k) && typeof it[k] === "string");
          return (
            <div className="card" key={i}>
              <div className="title">{tk ? it[tk] : `Option ${i + 1}`}</div>
              <dl>
                {Object.entries(it).filter(([k]) => k !== tk).map(([k, v]) => (
                  <div key={k} style={{ display: "contents" }}><dt>{pretty(k)}</dt><dd>{fmtVal(k, v)}</dd></div>
                ))}
              </dl>
            </div>
          );
        })}
      </div>
    </>
  );
}

export default function Result({ data }) {
  const p = findProb(data);
  const pct = p ? (p.v <= 1 ? p.v * 100 : p.v) : null;
  const lvl = pct == null ? null : pct >= 60 ? ["High risk", "var(--risk)"] : pct >= 30 ? ["Medium risk", "var(--amber)"] : ["Low risk", "var(--safe)"];
  const scalars = Object.fromEntries(Object.entries(data).filter(([k, v]) => v !== null && typeof v !== "object" && (!p || k !== p.key)));
  const known = ["financial_impact", "shap_explanations", "what_if_interventions"];
  const extras = Object.entries(data).filter(([k, v]) => v && typeof v === "object" && !known.includes(k) && !(p && findProb({ x: v })));

  return (
    <>
      {p && (
        <div className="hero">
          <div className="big" style={{ color: lvl[1] }}>{pct.toFixed(1)}%</div>
          <div className="meter">
            <span className="pill" style={{ color: lvl[1] }}>{lvl[0]}</span>
            <p className="hint">Chance this customer leaves ({pretty(p.key)})</p>
            <div className="bar"><i style={{ width: Math.min(100, pct) + "%", background: lvl[1] }} /></div>
          </div>
        </div>
      )}
      {Object.keys(scalars).length > 0 && <Stats obj={scalars} />}
      {data.financial_impact && <Stats obj={data.financial_impact} />}
      {Array.isArray(data.shap_explanations) && data.shap_explanations.length > 0 && <Shap items={data.shap_explanations} />}
      {Array.isArray(data.what_if_interventions) && data.what_if_interventions.length > 0 && <Interventions items={data.what_if_interventions} />}
      {extras.map(([k, v]) => (<div key={k}><h3>{pretty(k)}</h3><pre>{JSON.stringify(v, null, 2)}</pre></div>))}
      <details><summary>Raw response</summary><pre>{JSON.stringify(data, null, 2)}</pre></details>
    </>
  );
}
