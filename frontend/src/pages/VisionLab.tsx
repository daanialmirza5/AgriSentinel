import { useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { InspectionT, ModelStatusT } from "../types";
import { ConfidenceBar, EmptyState, Loading, StatusBadge, WarningBanner } from "../components/common";
import { useEffect } from "react";

export default function VisionLab() {
  const { selectedFieldId } = useFieldContext();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [kind, setKind] = useState<"image" | "video">("image");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InspectionT | null>(null);
  const [model, setModel] = useState<ModelStatusT | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<ModelStatusT>("/model/status").then(setModel);
  }, []);

  function onFileChange(f: File | null) {
    setFile(f);
    setResult(null);
    setError(null);
    if (f) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
      setKind(f.type.startsWith("video") ? "video" : "image");
    } else {
      setPreviewUrl(null);
    }
  }

  async function loadSample() {
    setError(null);
    setResult(null);
    const res = await fetch("/media/sample/synthetic_demo_field.jpg");
    const blob = await res.blob();
    const f = new File([blob], "synthetic_demo_field.jpg", { type: "image/jpeg" });
    onFileChange(f);
  }

  async function runInference() {
    if (!file || !selectedFieldId) return;
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const path = kind === "image" ? "/inspect/image" : "/inspect/video";
      const res = await api.post<InspectionT>(`${path}?field_id=${selectedFieldId}`, form);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!selectedFieldId) {
    return <EmptyState title="No field selected" hint="Create and select a field first (see Settings)." />;
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Vision Lab</h1>
          <p className="page-subtitle">Upload an image or video and run real detection inference.</p>
        </div>
      </div>

      {model?.warning && <WarningBanner>{model.warning}</WarningBanner>}

      <div className="grid grid-cols-2">
        <div className="card">
          <div className="section-title">1. Provide an image or video</div>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,video/mp4,video/avi,video/quicktime,video/x-matroska"
            onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          />
          <div className="flex gap-8 mt-8">
            <button className="btn btn-sm" onClick={loadSample}>Load synthetic demo sample</button>
          </div>

          {previewUrl && (
            <div className="mt-16">
              {kind === "image" ? (
                <img src={previewUrl} style={{ width: "100%", borderRadius: 8 }} />
              ) : (
                <video src={previewUrl} controls style={{ width: "100%", borderRadius: 8 }} />
              )}
            </div>
          )}

          <div className="flex gap-8 mt-16">
            <button className="btn btn-primary" disabled={!file || busy} onClick={runInference}>
              {busy ? <Loading label="Running inference..." /> : "Run Inference"}
            </button>
          </div>
          {error && <div className="danger-banner mt-16">{error}</div>}
        </div>

        <div className="card">
          <div className="section-title">2. Result</div>
          {!result && !busy && <EmptyState icon="🔬" title="No inspection run yet" />}
          {busy && <Loading label="Processing on CPU — this can take a few seconds..." />}
          {result && (
            <div>
              <div className="flex gap-8 items-center mt-8">
                <span className="badge badge-blue">{result.detection_mode.replace(/_/g, " ")}</span>
                <span className="text-dim">{result.processing_time_ms.toFixed(0)} ms</span>
                <span className="text-dim">model: {result.model_name}</span>
              </div>
              {result.annotated_asset_path && (
                <img src={result.annotated_asset_path} style={{ width: "100%", borderRadius: 8, marginTop: 12 }} />
              )}
              {result.error_message && <div className="warning-banner mt-8">{result.error_message}</div>}
              <div className="mt-16">
                <strong>{result.detection_count}</strong> detection(s)
              </div>
              {result.detections && result.detections.length > 0 && (
                <table className="mt-8">
                  <thead>
                    <tr>
                      <th>Class</th>
                      <th>Type</th>
                      <th>Confidence</th>
                      <th>Field coords</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.detections.map((d) => (
                      <tr key={d.id}>
                        <td>{d.class_name}</td>
                        <td><StatusBadge status={d.target_type} /></td>
                        <td><ConfidenceBar value={d.confidence} /></td>
                        <td className="mono text-dim">
                          {d.field_x !== null ? `${d.field_x.toFixed(2)}, ${d.field_y?.toFixed(2)} m (${d.localization_confidence})` : "unavailable"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
