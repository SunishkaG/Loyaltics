import { useEffect, useState } from "react";
import { auditLogs } from "./api.js";
import { pretty } from "./util.js";

export default function AuditLog() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    auditLogs()
      .then(d => setRows(Array.isArray(d) ? d : d.logs || d.audit_logs || d.data || [d]))
      .catch(e => setError(e.message));
  }, []);

  if (error) return <div className="err">{error}</div>;
  if (!rows) return <div className="empty">Loading…</div>;
  if (!rows.length) return <div className="empty">No predictions have been logged yet.</div>;

  const cols = [...new Set(rows.flatMap(r => (typeof r === "object" ? Object.keys(r) : [])))];
  if (!cols.length) return <pre>{JSON.stringify(rows, null, 2)}</pre>;

  return (
    <div className="scroll">
      <table>
        <thead><tr>{cols.map(c => <th key={c}>{pretty(c)}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map(c => (
                <td key={c}>{r[c] === undefined ? "" : typeof r[c] === "object" ? JSON.stringify(r[c]) : String(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
