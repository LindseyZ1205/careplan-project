import { useState, useEffect, useRef, useCallback } from "react";

const initialForm = {
  patient_first_name: "",
  patient_last_name: "",
  patient_mrn: "",
  doctor_name: "",
  doctor_npi: "",
  diagnosis: "",
  medication_name: "",
  notes: "",
};

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [careplanId, setCareplanId] = useState(null);
  const [pollStatus, setPollStatus] = useState(null);
  const [content, setContent] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [polling, setPolling] = useState(false);
  const intervalRef = useRef(null);

  const clearPoll = useCallback(() => {
    if (intervalRef.current != null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setPolling(false);
  }, []);

  const checkStatus = useCallback(
    async (id) => {
      try {
        const res = await fetch(`/api/careplan/${id}/status/`);
        if (!res.ok) {
          setError("Status request failed");
          clearPoll();
          return;
        }
        const data = await res.json();
        setPollStatus(data.status);

        if (data.status === "completed") {
          setContent(data.content ?? "");
          clearPoll();
        } else if (data.status === "failed") {
          setError(data.error || "Care plan generation failed.");
          clearPoll();
        }
      } catch {
        setError("Network error while polling status.");
        clearPoll();
      }
    },
    [clearPoll]
  );

  useEffect(() => {
    if (careplanId == null) return undefined;

    setPolling(true);
    setPollStatus("pending");
    setContent(null);
    setError(null);

    void checkStatus(careplanId);
    intervalRef.current = setInterval(() => {
      void checkStatus(careplanId);
    }, 3000);

    return () => {
      clearPoll();
    };
  }, [careplanId, checkStatus, clearPoll]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setContent(null);
    setCareplanId(null);
    clearPoll();

    try {
      const res = await fetch("/api/careplan/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || `Submit failed (${res.status})`);
        return;
      }
      if (data.careplan_id == null) {
        setError("No careplan_id in response");
        return;
      }
      setCareplanId(data.careplan_id);
    } catch {
      setError("Network error on submit.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Care Plan (React + polling)</h1>
        <p style={styles.desc}>
          Submit → receive <code>careplan_id</code> → poll{" "}
          <code>/api/careplan/&lt;id&gt;/status/</code> every 3s until{" "}
          <code>completed</code> or <code>failed</code>.
        </p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.row}>
            <Field label="Patient first name" name="patient_first_name" form={form} onChange={onChange} required />
            <Field label="Patient last name" name="patient_last_name" form={form} onChange={onChange} required />
          </div>
          <div style={styles.row}>
            <Field label="MRN (optional)" name="patient_mrn" form={form} onChange={onChange} />
            <Field label="Doctor / provider" name="doctor_name" form={form} onChange={onChange} required />
          </div>
          <div style={styles.row}>
            <Field label="NPI (optional)" name="doctor_npi" form={form} onChange={onChange} />
            <Field label="Diagnosis" name="diagnosis" form={form} onChange={onChange} required />
          </div>
          <label style={styles.label}>
            Medication name
            <input
              name="medication_name"
              value={form.medication_name}
              onChange={onChange}
              required
              style={styles.input}
            />
          </label>
          <label style={styles.label}>
            Notes (optional)
            <textarea name="notes" value={form.notes} onChange={onChange} rows={3} style={styles.textarea} />
          </label>
          <button type="submit" disabled={submitting} style={styles.btn}>
            {submitting ? "Submitting…" : "Submit"}
          </button>
        </form>

        {careplanId != null && (
          <section style={styles.section}>
            <h2 style={styles.h2}>Queue</h2>
            <p style={styles.meta}>
              <code>careplan_id</code>: <strong>{careplanId}</strong>
              {polling && (
                <>
                  {" "}
                  · polling… (every 3s) · current: <strong>{pollStatus ?? "…"}</strong>
                </>
              )}
            </p>
          </section>
        )}

        {content != null && (
          <section style={styles.section}>
            <h2 style={styles.h2}>Care plan</h2>
            <pre style={styles.pre}>{content}</pre>
          </section>
        )}

        {error != null && (
          <section style={styles.section}>
            <h2 style={styles.h2Error}>Error</h2>
            <p style={styles.errText}>{error}</p>
          </section>
        )}
      </div>
    </div>
  );
}

function Field({ label, name, form, onChange, required }) {
  return (
    <label style={styles.label}>
      {label}
      <input name={name} value={form[name]} onChange={onChange} required={required} style={styles.input} />
    </label>
  );
}

const styles = {
  wrap: { maxWidth: 720, margin: "0 auto" },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "24px 28px",
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
  },
  h1: { margin: "0 0 8px", fontSize: "1.6rem" },
  h2: { margin: "0 0 8px", fontSize: "1.1rem" },
  h2Error: { margin: "0 0 8px", fontSize: "1.1rem", color: "#b91c1c" },
  desc: { margin: "0 0 20px", color: "#4b5563", fontSize: "0.95rem", lineHeight: 1.5 },
  form: { display: "flex", flexDirection: "column", gap: 14 },
  row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 },
  label: { display: "flex", flexDirection: "column", gap: 6, fontWeight: 600, fontSize: "0.88rem", color: "#374151" },
  input: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: "8px 10px",
    fontSize: "0.95rem",
  },
  textarea: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: "8px 10px",
    fontSize: "0.95rem",
    resize: "vertical",
  },
  btn: {
    alignSelf: "flex-start",
    marginTop: 4,
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 999,
    padding: "10px 20px",
    fontWeight: 600,
    cursor: "pointer",
  },
  section: { marginTop: 24, paddingTop: 20, borderTop: "1px solid #e5e7eb" },
  meta: { margin: 0, fontSize: "0.9rem", color: "#374151" },
  pre: {
    margin: 0,
    background: "#0b1120",
    color: "#e5e7eb",
    padding: 16,
    borderRadius: 10,
    fontSize: "0.82rem",
    whiteSpace: "pre-wrap",
    overflowX: "auto",
  },
  errText: { margin: 0, color: "#b91c1c", fontSize: "0.95rem" },
};
