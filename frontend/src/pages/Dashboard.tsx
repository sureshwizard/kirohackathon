// src/pages/Dashboard.tsx
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { EXPENSES_API } from "../config";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

type CatRow = { exp_type: string; total: number; count: number };
type DayRow = { day: string; total: number }; // expected shape if backend returns by_day

const COLORS = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC949", "#AF7AA1", "#FF9DA7"];

function currencyFmt(n = 0) {
  // indian-style formatting with rupee symbol (simple)
  const sign = n < 0 ? "-" : "";
  const v = Math.abs(n).toFixed(2);
  return sign + "₹" + v;
}

export default function Dashboard(): JSX.Element {
  const [data, setData] = useState<CatRow[] | null>(null);
  const [daily, setDaily] = useState<DayRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth() + 1;
    setLoading(true);
    axios
      .get(`${EXPENSES_API}/reports/monthly?year=${y}&month=${m}`)
      .then((r) => {
        // backend expected to return { by_category: [...], by_day: [...] } optionally
        const res = r.data || {};
        setData(res.by_category ?? res.categories ?? []);
        setDaily(res.by_day ?? res.daily ?? null);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load dashboard data");
      })
      .finally(() => setLoading(false));
  }, []);

 // compute income, expense, net separately
  const totals = useMemo(() => {
    if (!data || data.length === 0) return { income: 0, expense: 0, net: 0, txCount: 0, avg: 0 };
    const income = data.reduce((s, d) => s + (Number(d.total) > 0 ? Number(d.total) : 0), 0);
    const expense = data.reduce((s, d) => s + (Number(d.total) < 0 ? Number(d.total) : 0), 0); // negative
    const txCount = data.reduce((s, d) => s + (Number(d.count) || 0), 0);
    const net = income + expense; // expense is negative
    const avg = txCount ? net / txCount : 0;
    return { income, expense, net, txCount, avg };
  }, [data]);

  // prepare data for charts
   // bar & pie charts should show magnitude (absolute values)
  const barData = (data ?? []).map((d) => ({
    ...d,
    abs_total: Math.abs(Number(d.total) || 0),
  }));
  const pieData = (data ?? []).map((d) => ({
    name: d.exp_type,
    value: Math.abs(Number(d.total) || 0),
  }));

  const lineData = daily ?? [];

  return (
    <div style={{ maxWidth: 1100, margin: "1rem auto", fontFamily: "system-ui", padding: "0 12px" }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div>
          <h2 style={{ margin: 0 }}>Dashboard</h2>
          <p style={{ margin: 0, color: "#666" }}>Monthly category totals</p>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {/* quick stat cards */}
          <div style={cardStyle}>
            <div style={cardTitle}>Income</div>
            <div style={cardValue}>{currencyFmt(totals.income)}</div>
            <div style={cardSub}>{totals.txCount} transactions</div>
          </div>

          <div style={cardStyle}>
            <div style={cardTitle}>Expense</div>
            <div style={cardValue}>{currencyFmt(Math.abs(totals.expense))}</div>
            <div style={cardSub}>Total outflow</div>
          </div>

          <div style={cardStyle}>
            <div style={cardTitle}>Net</div>
            <div
              style={{
                ...cardValue,
                color: totals.net < 0 ? "#E15759" : "#2E7D32",
              }}
            >
              {currencyFmt(totals.net)}
            </div>
            <div style={cardSub}>Income − Expense</div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="card" style={{ padding: 20 }}>Loading...</div>
      ) : error ? (
        <div className="card" style={{ padding: 20, color: "crimson" }}>{error}</div>
      ) : !data || data.length === 0 ? (
        <div className="card" style={{ padding: 20 }}>No data for this month</div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 16 }}>
          {/* Left column: bar + line */}
          <div className="card" style={{ padding: 12 }}>
            <h3 style={{ marginTop: 6 }}>Category totals</h3>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 10, right: 10, left: 0, bottom: 40 }}>
                  <XAxis dataKey="exp_type" tick={{ fontSize: 12 }} interval={0} angle={-30} textAnchor="end" height={60} />
                  <YAxis />
                  <Tooltip formatter={(v: any) => currencyFmt(Number(v))} />
                  <Legend />
                  <Bar dataKey="abs_total" fill="#4E79A7" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {lineData && lineData.length > 0 ? (
              <>
                <h4 style={{ marginTop: 12 }}>Daily trend</h4>
                <div style={{ height: 220 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={lineData} margin={{ top: 5, right: 10, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis />
                      <Tooltip formatter={(v: any) => currencyFmt(Number(v))} />
                      <Line type="monotone" dataKey="total" stroke="#E15759" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            ) : (
              <div style={{ marginTop: 14, color: "#666" }}>
                No daily series available. To show a daily trend, have the backend return a <code>by_day</code> array like:
                <pre style={{ background: "#fafafa", padding: 8, marginTop: 8 }}>
{`"by_day": [{ "day": "01", "total": 1200 }, { "day": "02", "total": 900 }, ...]`}
                </pre>
              </div>
            )}
          </div>

          {/* Right column: pie + category list */}
          <div className="card" style={{ padding: 12 }}>
            <h3 style={{ marginTop: 6 }}>Category distribution</h3>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    label={(entry: any) => entry.name}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any) => currencyFmt(Number(v))} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <h4 style={{ marginTop: 12 }}>Top categories</h4>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {barData
                .slice()
                .sort((a, b) => Math.abs(b.total) - Math.abs(a.total))
                .slice(0, 8)
                .map((d, i) => (
                  <li key={d.exp_type} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px dashed #eee" }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span style={{ width: 10, height: 10, background: COLORS[i % COLORS.length], display: "inline-block", borderRadius: 2 }} />
                      <strong>{d.exp_type}</strong>
                      <span style={{ color: "#666", marginLeft: 6 }}>({d.count})</span>
                    </div>
                    <div style={{ color: d.total < 0 ? "#E15759" : "#333" }}>{currencyFmt(d.total)}</div>
                  </li>
                ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

/* small inline styles */
const cardStyle: React.CSSProperties = {
  background: "#fff",
  borderRadius: 8,
  boxShadow: "0 1px 4px rgba(20,20,30,0.04)",
  padding: 12,
  minWidth: 140,
  textAlign: "left",
};

const cardTitle: React.CSSProperties = { fontSize: 12, color: "#666" };
const cardValue: React.CSSProperties = { fontSize: 18, fontWeight: 700, marginTop: 6 };
const cardSub: React.CSSProperties = { fontSize: 12, color: "#888", marginTop: 4 };
