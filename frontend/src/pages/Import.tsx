// src/pages/Import.tsx
import React, { useState, useRef } from "react";
import axios from "axios";
import { INGEST_API } from "../config";

export default function ImportPage(): JSX.Element {
  const [source, setSource] = useState("generic");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any | null>(null);
  const [dedupe, setDedupe] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importedCount, setImportedCount] = useState<number | null>(null);
  const [lastBatchId, setLastBatchId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPreview(null);
    setDedupe(null);
    setImportedCount(null);
    setError(null);
    setLastBatchId(null);
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setDedupe(null);
    setImportedCount(null);
    setError(null);
    setLastBatchId(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const doPreview = async () => {
    if (!file) return alert("Select a file first");
    setError(null);
    setLoading(true);
    setPreview(null);
    setDedupe(null);
    try {
      const fd = new FormData();
      fd.append("source", source);
      fd.append("file", file);
      fd.append("rows", "10");

      const res = await axios.post(`${INGEST_API}/preview_csv`, fd);
      setPreview(res.data);

      const rowsForDedupe = res.data.parsed ?? res.data.preview ?? [];
      try {
        if (Array.isArray(rowsForDedupe) && rowsForDedupe.length > 0) {
          const ded = await axios.post(`${INGEST_API}/dedupe_preview`, rowsForDedupe);
          setDedupe(ded.data);
        } else {
          setDedupe(null);
        }
      } catch {
        setDedupe(null);
      }
    } catch (err: any) {
      console.error("preview error", err);
      const msg = err?.response?.data?.detail || err?.response?.data || err?.message || "Preview failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  const doImport = async () => {
    if (!file) return alert("Select a file first");
    setError(null);
    setLoading(true);
    setImportedCount(null);
    setLastBatchId(null);
    try {
      const fd = new FormData();
      fd.append("source", source);
      fd.append("file", file);

      const res = await axios.post<{ imported?: number; batch_id?: string }>(`${INGEST_API}/upload_csv`, fd, {
        timeout: 120000,
      });

      const imported = res.data.imported ?? 0;
      setImportedCount(imported);
      if (res.data.batch_id) setLastBatchId(res.data.batch_id);

      if (fileInputRef.current) fileInputRef.current.value = "";
      setFile(null);
    } catch (err: any) {
      console.error("import error", err);
      const msg = err?.response?.data?.detail || err?.response?.data || err?.message || "Import failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  const cancelImport = async (batchId: string) => {
    if (!batchId) return;
    if (!window.confirm("Cancel this import and delete inserted rows?")) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.delete<{ deleted: number; batch_id: string }>(`${INGEST_API}/cancel_import/${batchId}`);
      alert(`Deleted ${resp.data.deleted} rows from batch ${resp.data.batch_id}`);
      setLastBatchId(null);
      setImportedCount(null);
      setPreview(null);
      setDedupe(null);
    } catch (err: any) {
      console.error("cancel import error", err);
      const msg = err?.response?.data?.detail || err?.response?.data || err?.message || "Cancel failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  const canReset = !!(file || preview || dedupe || importedCount || error || lastBatchId);

  return (
    <div>
      <div className="card">
        <h2>Import Transactions</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <select value={source} onChange={e => setSource(e.target.value)}>
            <option value="amazon">Amazon</option>
            <option value="gpay">Google Pay</option>
            <option value="paytm">Paytm</option>
            <option value="phonepe">PhonePe</option>
            <option value="bank">Bank/Card</option>
            <option value="generic">Generic</option>
          </select>

          <input
            ref={fileInputRef}
            type="file"
            onChange={onFileChange}
            accept=".csv,text/csv"
          />

          <button onClick={doPreview} disabled={loading}>
            {loading ? "Loading..." : "Preview"}
          </button>

          <button onClick={doImport} disabled={loading}>
            {loading ? "Importing..." : "Import"}
          </button>

          <button onClick={handleReset} disabled={loading || !canReset}>
            Reset
          </button>

          {lastBatchId && (
            <button onClick={() => cancelImport(lastBatchId)} disabled={loading}>
              Cancel Import
            </button>
          )}
        </div>

        {error && (
          <div style={{ color: "crimson", marginTop: 8 }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {lastBatchId && (
          <div style={{ marginTop: 8, fontSize: 13 }}>
            Last batch: <code>{lastBatchId}</code>
          </div>
        )}

        {importedCount !== null && (
          <div style={{ marginTop: 8, color: "green" }}>
            Imported rows: <strong>{importedCount}</strong>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h4>Preview</h4>
        {preview ? (
          <>
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(preview, null, 2)}</pre>
            {preview.rows_raw && (
              <>
                <h5 style={{ marginTop: 12 }}>Raw CSV rows (first few)</h5>
                <pre style={{ maxHeight: 200, overflow: "auto", background: "#f7f7f7", padding: 8 }}>
                  {JSON.stringify(preview.rows_raw, null, 2)}
                </pre>
              </>
            )}
          </>
        ) : (
          <p>No preview yet</p>
        )}
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h4>Dedupe Preview</h4>
        {dedupe ? (
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(dedupe, null, 2)}</pre>
        ) : (
          <p>No dedupe results</p>
        )}
      </div>
    </div>
  );
}
