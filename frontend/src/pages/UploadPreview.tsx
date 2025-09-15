import React, { useState, useRef } from "react";
import axios from "axios";
import { EXPENSES_API, INGEST_API } from "../config";

type HeaderRow = {
  row_index: number;
  tx_datetime: string | null;
  exp_type: string;
  total_amount: number;
  note: string;
  source: string;
  txn_id: string | null;
};

type DetailRow = {
  row_index: number;
  item_name: string;
  quantity: number;
  amount: number;
  linked_header_index: number | null;
  linked_header_txn: string | null;
};

export default function UploadPreview(): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState<string>("generic");
  const [preview, setPreview] = useState<{ headers: HeaderRow[]; details: DetailRow[] } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [strict, setStrict] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const handleFile = (ev: React.ChangeEvent<HTMLInputElement>) => {
    setMessage(null);
    const f = ev.target.files && ev.target.files[0];
    setFile(f ?? null);
    setPreview(null);
  };

  const doPreview = async () => {
  if (!file) {
    setMessage("Choose a CSV file first.");
    return;
  }
  setLoadingPreview(true);
  setMessage(null);
  try {
    const form = new FormData();
    form.append("source", source);
    form.append("file", file);
    const res = await axios.post(`${INGEST_API}/preview_csv`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    // Backend may return two shapes:
    // 1) new: { headers: [...], details: [...] }
    // 2) old: { parsed: [...] }  (each parsed row -> header)
    const data = res.data ?? {};

    if (data.headers || data.details) {
      setPreview({ headers: data.headers ?? [], details: data.details ?? [] });
    } else if (Array.isArray(data.parsed)) {
      // map old "parsed" array to header shape
      const mappedHeaders = data.parsed.map((p: any, i: number) => ({
        row_index: i,
        tx_datetime: p.tx_datetime ?? p.date ?? null,
        exp_type: p.exp_type ?? "",
        total_amount: typeof p.total_amount === "number" ? p.total_amount : parseFloat(p.total_amount || 0),
        note: p.note ?? p.Description ?? "",
        source: p.source ?? source,
        txn_id: p.txn_id ?? p.TxnID ?? null,
      }));
      setPreview({ headers: mappedHeaders, details: [] });
    } else {
      // unknown response
      setPreview({ headers: [], details: [] });
      setMessage("Preview returned no rows.");
    }
  } catch (err: any) {
    console.error("preview error", err);
    const body = err?.response?.data;
    setMessage(body ? (body.detail ?? JSON.stringify(body)) : "Failed to preview CSV");
  } finally {
    setLoadingPreview(false);
  }
};


  const doUpload = async () => {
    if (!file) {
      setMessage("Choose a CSV file first.");
      return;
    }
    setUploading(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append("source", source);
      form.append("file", file);
      form.append("strict_details", strict ? "true" : "false");
      const res = await axios.post(`${INGEST_API}/upload_csv`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage(`Imported ${res.data.imported_expenses} expenses and ${res.data.imported_items} items.`);
      // clear preview and input for next upload
      setPreview(null);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: any) {
      console.error("upload error", err);
      setMessage(err?.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "1.25rem auto", fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto" }}>
      <h3>CSV Upload & Preview</h3>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <input ref={fileRef} type="file" accept=".csv,text/csv" onChange={handleFile} />
        <label>
          Source:
          <select value={source} onChange={(e) => setSource(e.target.value)} style={{ marginLeft: 6 }}>
            <option value="generic">generic</option>
            <option value="gpay">gpay</option>
            <option value="bank">bank</option>
          </select>
        </label>

        <label style={{ marginLeft: 12 }}>
          <input type="checkbox" checked={strict} onChange={(e) => setStrict(e.target.checked)} /> Strict details
        </label>

        <button onClick={doPreview} disabled={!file || loadingPreview} style={{ marginLeft: "auto" }}>
          {loadingPreview ? "Previewing…" : "Preview CSV"}
        </button>

        <button onClick={doUpload} disabled={!file || uploading} style={{ marginLeft: 8 }}>
          {uploading ? "Uploading…" : "Upload CSV"}
        </button>
      </div>

      {message && (
        <div style={{ marginBottom: 12, color: message.startsWith("Imported") ? "green" : "crimson" }}>{message}</div>
      )}

      {preview && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 12 }}>
          <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 8, background: "#fff" }}>
            <h4 style={{ marginTop: 0 }}>Headers ({preview.headers.length})</h4>
            <div style={{ maxHeight: 380, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
                    <th style={{ padding: 6 }}>#</th>
                    <th style={{ padding: 6 }}>Date</th>
                    <th style={{ padding: 6 }}>Note</th>
                    <th style={{ padding: 6 }}>Amount</th>
                    <th style={{ padding: 6 }}>TxnID</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.headers.map((h, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #fafafa" }}>
                      <td style={{ padding: 6 }}>{i + 1}</td>
                      <td style={{ padding: 6 }}>{h.tx_datetime ?? "-"}</td>
                      <td style={{ padding: 6 }}>{h.note ?? "-"}</td>
                      <td style={{ padding: 6 }}>{h.total_amount?.toFixed?.(2) ?? "-"}</td>
                      <td style={{ padding: 6 }}>{h.txn_id ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 8, background: "#fff" }}>
            <h4 style={{ marginTop: 0 }}>Details ({preview.details.length})</h4>
            <div style={{ maxHeight: 380, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
                    <th style={{ padding: 6 }}>#</th>
                    <th style={{ padding: 6 }}>Item</th>
                    <th style={{ padding: 6 }}>Qty</th>
                    <th style={{ padding: 6 }}>Amount</th>
                    <th style={{ padding: 6 }}>Linked Header #</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.details.map((d, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #fafafa" }}>
                      <td style={{ padding: 6 }}>{i + 1}</td>
                      <td style={{ padding: 6 }}>{d.item_name ?? "-"}</td>
                      <td style={{ padding: 6 }}>{d.quantity}</td>
                      <td style={{ padding: 6 }}>{d.amount?.toFixed?.(2) ?? "-"}</td>
                      <td style={{ padding: 6 }}>{d.linked_header_index !== null ? d.linked_header_index + 1 : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
