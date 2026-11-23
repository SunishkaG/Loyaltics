import { useState } from "react";

const STATES = ["Delhi NCR", "Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "West Bengal", "Uttar Pradesh", "Telangana"];
const NUMERIC = ["CIBIL_Score", "Age", "Tenure_Years", "Balance_INR", "Num_Of_Products", "Has_Credit_Card", "UPI_Active_User", "Annual_Income_INR"];

export const DEFAULTS = {
  CIBIL_Score: 300, State: "Delhi NCR", Gender: "Female", Age: 46, Tenure_Years: 2,
  Balance_INR: 950000, Num_Of_Products: 1, Has_Credit_Card: 1, UPI_Active_User: 0, Annual_Income_INR: 1400000,
};

function Field({ label, name, form, set, full, ...rest }) {
  return (
    <div className={full ? "full" : ""}>
      <label htmlFor={name}>{label}</label>
      <input id={name} value={form[name]} onChange={e => set(name, e.target.value)} required {...rest} />
    </div>
  );
}
function YesNo({ label, name, form, set }) {
  return (
    <div>
      <label htmlFor={name}>{label}</label>
      <select id={name} value={form[name]} onChange={e => set(name, e.target.value)}>
        <option value="1">Yes</option>
        <option value="0">No</option>
      </select>
    </div>
  );
}

export default function CustomerForm({ onSubmit, loading }) {
  const [form, setForm] = useState(DEFAULTS);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = e => {
    e.preventDefault();
    const body = {};
    for (const [k, v] of Object.entries(form)) body[k] = NUMERIC.includes(k) ? Number(v) : v;
    onSubmit(body);
  };

  return (
    <form className="grid" onSubmit={submit}>
      <Field label="CIBIL score" name="CIBIL_Score" type="number" min="300" max="900" form={form} set={set} />
      <Field label="Age" name="Age" type="number" min="18" max="100" form={form} set={set} />
      <div>
        <label htmlFor="State">State</label>
        <input id="State" list="states" value={form.State} onChange={e => set("State", e.target.value)} required />
        <datalist id="states">{STATES.map(s => <option key={s}>{s}</option>)}</datalist>
      </div>
      <div>
        <label htmlFor="Gender">Gender</label>
        <select id="Gender" value={form.Gender} onChange={e => set("Gender", e.target.value)}>
          <option>Female</option><option>Male</option>
        </select>
      </div>
      <Field label="Tenure (years)" name="Tenure_Years" type="number" min="0" form={form} set={set} />
      <Field label="Products held" name="Num_Of_Products" type="number" min="1" form={form} set={set} />
      <Field label="Account balance (₹)" name="Balance_INR" type="number" min="0" full form={form} set={set} />
      <Field label="Annual income (₹)" name="Annual_Income_INR" type="number" min="0" full form={form} set={set} />
      <YesNo label="Credit card" name="Has_Credit_Card" form={form} set={set} />
      <YesNo label="Active on UPI" name="UPI_Active_User" form={form} set={set} />
      <div className="full actions">
        <button className="primary" disabled={loading}>{loading ? "Analysing…" : "Predict churn"}</button>
        <button type="button" onClick={() => setForm(DEFAULTS)}>Reset</button>
      </div>
    </form>
  );
}
