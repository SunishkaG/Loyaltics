import { useEffect, useState } from "react";
import CustomerForm from "./CustomerForm.jsx";
import Result from "./Result.jsx";
import AuditLog from "./AuditLog.jsx";
import { health, predict } from "./api.js";

export default function App() {
  const [tab, setTab] = useState("prediction");
  const [status, setStatus] = useState("unknown"); // ok | bad | unknown
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const ping = () => health().then(() => setStatus("ok")).catch(() => setStatus("bad"));
  useEffect(() => { ping(); }, []);

  const run = async body => {
    setLoading(true); setError(null);
    try { setResult(await predict(body)); setStatus("ok"); }
    catch (e) {
      setResult(null);
      setError(e instanceof TypeError ? "Could not reach the API. Check that the backend is running on port 8000." : e.message);
      if (e instanceof TypeError) setStatus("bad");
    } finally { setLoading(false); }
  };

  return (
    <>
      <header>
        <h1>Loyaltics <small>Churn prediction, explanation and what-if simulation</small></h1>
        <div className="conn">
          <span className={"dot " + (status === "unknown" ? "" : status)} title={"API " + status} />
          <span>{status === "ok" ? "API connected" : status === "bad" ? "API unreachable" : "Checking…"}</span>
          <button onClick={ping}>Check API</button>
        </div>
      </header>
      <main>
        <section className="panel">
          <h2>Customer profile</h2>
          <CustomerForm onSubmit={run} loading={loading} />
        </section>
        <section className="panel">
          <div className="tabs" role="tablist">
            {[["prediction", "Prediction"], ["audit", "Audit log"]].map(([id, label]) => (
              <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>{label}</button>
            ))}
          </div>
          {tab === "prediction" ? (
            error ? <div className="err">{error}</div>
            : result ? <Result data={result} />
            : <div className="empty">Fill in a customer profile and select <b>Predict churn</b> to see the risk, the drivers behind it and suggested retention actions.</div>
          ) : <AuditLog />}
        </section>
      </main>
    </>
  );
}
