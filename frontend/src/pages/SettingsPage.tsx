import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { ModelStatusT } from "../types";
import { EmptyState, WarningBanner } from "../components/common";

export default function SettingsPage() {
  const { fields, refreshFields, selectedFieldId, setSelectedFieldId } = useFieldContext();
  const [model, setModel] = useState<ModelStatusT | null>(null);
  const [settings, setSettings] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [newField, setNewField] = useState({ name: "", crop_type: "corn", width_m: 20, length_m: 15, row_spacing_m: 0.5 });

  async function loadAll() {
    const [m, s] = await Promise.all([api.get<ModelStatusT>("/model/status"), api.get<{ values: Record<string, any> }>("/settings")]);
    setModel(m);
    setSettings(s.values);
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function createField(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await api.post<{ id: string }>("/fields", {
        ...newField,
        configuration: { is_demo: false, rover_start: { x: 0.5, y: 0.5 } },
      });
      await refreshFields();
      setSelectedFieldId(created.id);
      setNewField({ name: "", crop_type: "corn", width_m: 20, length_m: 15, row_spacing_m: 0.5 });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }

  async function createDemoField() {
    const created = await api.post<{ id: string }>("/fields", {
      name: `Demo Field ${new Date().toLocaleTimeString()}`,
      crop_type: "corn",
      width_m: 20,
      length_m: 15,
      row_spacing_m: 0.5,
      configuration: { is_demo: true, rover_start: { x: 0.5, y: 0.5 }, restricted_zones: [{ x1: 16, y1: 12, x2: 19, y2: 14, name: "buffer strip" }] },
    });
    await refreshFields();
    setSelectedFieldId(created.id);
  }

  async function deleteField(id: string) {
    if (!confirm("Delete this field and all its inspections/targets/history?")) return;
    await api.del(`/fields/${id}`);
    await refreshFields();
  }

  async function saveSettings() {
    if (!settings) return;
    await api.patch("/settings", { values: settings });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Model, field, and simulation configuration.</p>
        </div>
      </div>

      <div className="grid grid-cols-2">
        <div className="card">
          <div className="section-title">Model Status</div>
          {model && (
            <div className="flex-col gap-8">
              <Row k="Backend" v={model.backend} />
              <Row k="Loaded" v={String(model.loaded)} />
              <Row k="Label" v={model.label} />
              <Row k="Path" v={<span className="mono">{model.model_path || "—"}</span>} />
              <Row k="Task" v={model.task || "—"} />
              <Row k="Device" v={model.device} />
              {model.error && <Row k="Error" v={model.error} />}
            </div>
          )}
          {model?.warning && <WarningBanner>{model.warning}</WarningBanner>}
          <p className="text-faint" style={{ fontSize: 11.5 }}>
            To use a real trained weed/crop model, place a YOLO checkpoint at <span className="mono">models/weed_crop_model.pt</span> and restart the
            backend. See docs/DATASET_GUIDE.md.
          </p>
        </div>

        <div className="card">
          <div className="section-title">Detection &amp; Simulation Settings</div>
          {settings && (
            <div className="flex-col gap-12">
              <div>
                <label>Detection backend preference</label>
                <select value={settings.detection_backend_preference} onChange={(e) => setSettings({ ...settings, detection_backend_preference: e.target.value })}>
                  <option value="auto">Auto (prefer YOLO if available)</option>
                  <option value="classical">Classical vegetation heuristic only</option>
                </select>
              </div>
              <div>
                <label>Confidence threshold ({settings.confidence_threshold})</label>
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={settings.confidence_threshold}
                  onChange={(e) => setSettings({ ...settings, confidence_threshold: Number(e.target.value) })}
                />
              </div>
              <div>
                <label>Require operator approval before actuation</label>
                <select
                  value={String(settings.require_operator_approval)}
                  onChange={(e) => setSettings({ ...settings, require_operator_approval: e.target.value === "true" })}
                >
                  <option value="true">Required</option>
                  <option value="false">Not required (demo only)</option>
                </select>
              </div>
              <button className="btn btn-primary" onClick={saveSettings}>
                {saved ? "Saved ✓" : "Save Settings"}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 mt-16">
        <div className="card">
          <div className="section-title">Create Field</div>
          <form onSubmit={createField} className="flex-col gap-12">
            <div>
              <label>Name</label>
              <input type="text" required value={newField.name} onChange={(e) => setNewField({ ...newField, name: e.target.value })} className="w-full" />
            </div>
            <div className="grid grid-cols-2">
              <div>
                <label>Crop type</label>
                <input type="text" value={newField.crop_type} onChange={(e) => setNewField({ ...newField, crop_type: e.target.value })} className="w-full" />
              </div>
              <div>
                <label>Row spacing (m)</label>
                <input type="number" step={0.1} value={newField.row_spacing_m} onChange={(e) => setNewField({ ...newField, row_spacing_m: Number(e.target.value) })} className="w-full" />
              </div>
              <div>
                <label>Width (m)</label>
                <input type="number" value={newField.width_m} onChange={(e) => setNewField({ ...newField, width_m: Number(e.target.value) })} className="w-full" />
              </div>
              <div>
                <label>Length (m)</label>
                <input type="number" value={newField.length_m} onChange={(e) => setNewField({ ...newField, length_m: Number(e.target.value) })} className="w-full" />
              </div>
            </div>
            {error && <div className="danger-banner">{error}</div>}
            <div className="flex gap-8">
              <button className="btn btn-primary" type="submit">Create Field</button>
              <button className="btn" type="button" onClick={createDemoField}>Create Demo Field</button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="section-title">Manage Fields</div>
          {fields.length === 0 ? (
            <EmptyState title="No fields yet" />
          ) : (
            <table>
              <thead><tr><th>Name</th><th>Crop</th><th>Size</th><th></th></tr></thead>
              <tbody>
                {fields.map((f) => (
                  <tr key={f.id}>
                    <td>{f.name} {f.configuration?.is_demo && <span className="badge badge-amber">DEMO</span>}</td>
                    <td>{f.crop_type}</td>
                    <td>{f.width_m}×{f.length_m}m</td>
                    <td><button className="btn btn-sm btn-danger" onClick={() => deleteField(f.id)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: any }) {
  return (
    <div className="flex justify-between">
      <span className="text-dim">{k}</span>
      <span style={{ textAlign: "right", maxWidth: "60%" }}>{v}</span>
    </div>
  );
}
