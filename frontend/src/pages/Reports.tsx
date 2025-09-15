// src/pages/Reports.tsx
import React, { useState } from "react";
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
  CartesianGrid
} from "recharts";

function currencyFmt(n = 0) {
  const sign = n < 0 ? "-" : "";
  const v = Math.abs(n).toFixed(2);
  return sign + "₹" + v;
}

export default function Reports(): JSX.Element {
  const now = new Date();
  const [y1, setY1] = useState<number>(now.getFullYear());
  const [m1, setM1] = useState<number>(now.getMonth() + 1);
  const [y2, setY2] = useState<number>(now.getFullYear());
  const [m2, setM2] = useState<number>(Math.max(1, now.getMonth())); // previous month default
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const runCompare = () => {
    setLoading(true);
    axios.get(`${EXPENSES_API}/reports/compare?y1=${y1}&m1=${m1}&y2=${y2}&m2=${m2}`)
      .then(r => setResult(r.data))
      .catch(err => {
        console.error(err);
        alert("Compare failed: " + (err?.response?.data?.detail || err?.message));
      })
      .finally(() => setLoading(false));
  };

  const makeBarData = (by_category: any[]) => {
    return (by_category || []).map(it => ({ exp_type: it.exp_type, total: Math.abs(it.total) }));
  };

  const renderBar = (title: string, data: any[]) => (
    <div style={{flex: 1, minWidth: 320, height: 340, borderRadius: 8, padding: 12, boxShadow: '0 1px 6px rgba(0,0,0,0.06)', background:'#fff'}}>
      <h4 style={{marginTop: 0}}>{title}</h4>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="exp_type" angle={-30} textAnchor="end" interval={0} height={60} />
          <YAxis />
          <Tooltip formatter={(v:any) => currencyFmt(v)} />
          <Legend />
          <Bar dataKey="total" fill="#4E79A7" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <div style={{maxWidth: 1100, margin: '1rem auto', fontFamily: 'system-ui', padding: 12}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
        <div>
          <h2 style={{margin:0}}>Compare Two Months</h2>
          <p style={{margin:0,color:'#666'}}>Compare category totals between two months</p>
        </div>

        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <div style={{display:'flex', gap:6, alignItems:'center'}}>
            <small>Month 1</small>
            <input type="number" value={m1} onChange={e=>setM1(Number(e.target.value))} style={{width:70}} />
            <input type="number" value={y1} onChange={e=>setY1(Number(e.target.value))} style={{width:100}} />
          </div>
          <div style={{display:'flex', gap:6, alignItems:'center'}}>
            <small>Month 2</small>
            <input type="number" value={m2} onChange={e=>setM2(Number(e.target.value))} style={{width:70}} />
            <input type="number" value={y2} onChange={e=>setY2(Number(e.target.value))} style={{width:100}} />
          </div>
          <button onClick={runCompare} disabled={loading}>{loading ? 'Comparing...' : 'Compare'}</button>
        </div>
      </div>

      {!result ? (
        <div className="card" style={{padding:16}}>No comparison yet. Pick months and click Compare.</div>
      ) : (
        <>
          <div style={{display:'flex', gap:12, marginBottom:12, flexWrap:'wrap'}}>
            {renderBar(`${result.month1.month}/${result.month1.year}`, makeBarData(result.month1.by_category))}
            {renderBar(`${result.month2.month}/${result.month2.year}`, makeBarData(result.month2.by_category))}
          </div>

          <div className="card" style={{padding:12, marginTop:12}}>
            <h3 style={{marginTop:0}}>Category differences (month2 − month1)</h3>
            <table style={{width:'100%', borderCollapse:'collapse'}}>
              <thead>
                <tr style={{textAlign:'left', borderBottom:'1px solid #eee'}}>
                  <th>Category</th>
                  <th>Month1</th>
                  <th>Month2</th>
                  <th>Difference</th>
                </tr>
              </thead>
              <tbody>
                {result.diff_by_category.map((d:any) => (
                  <tr key={d.exp_type} style={{borderBottom:'1px dashed #f0f0f0'}}>
                    <td style={{padding:'8px 6px'}}><strong>{d.exp_type}</strong></td>
                    <td style={{padding:'8px 6px'}}>{currencyFmt(d.total1)}</td>
                    <td style={{padding:'8px 6px'}}>{currencyFmt(d.total2)}</td>
                    <td style={{padding:'8px 6px', color: d.diff < 0 ? '#E15759' : '#2E7D32'}}>{currencyFmt(d.diff)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
