import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { InspectionT } from "../types";
import { ConfidenceBar, EmptyState, StatusBadge } from "../components/common";

const PAGE_SIZE = 10;

export default function History() {
  const { selectedFieldId } = useFieldContext();
  const [inspections, setInspections] = useState<InspectionT[]>([]);
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<InspectionT | null>(null);
  const [search, setSearch] = useState("");

  async function refresh() {
    if (!selectedFieldId) return;
    const data = await api.get<InspectionT[]>(`/inspections?field_id=${selectedFieldId}&limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`);
    setInspections(data);
  }

  useEffect(() => {
    refresh();
  }, [selectedFieldId, page]);

  async function openDetail(id: string) {
    const detail = await api.get<InspectionT>(`/inspections/${id}`);
    setSelected(detail);
  }

  async function remove(id: string) {
    if (!confirm("Delete this inspection and its detections?")) return;
    await api.del(`/inspections/${id}`);
    setSelected(null);
    refresh();
  }

  const filtered = inspections.filter(
    (i) => !search || i.original_filename.toLowerCase().includes(search.toLowerCase()) || i.source_type.includes(search.toLowerCase())
  );

  if (!selectedFieldId) return <EmptyState title="No field selected" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Inspection History</h1>
          <p className="page-subtitle">Stored inspection and detection records.</p>
        </div>
        <input type="text" placeholder="Search filename or source..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="grid grid-cols-2">
        <div className="card">
          {filtered.length === 0 ? (
            <EmptyState icon="🗂️" title="No inspections recorded yet" hint="Run one from the Vision Lab." />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Source</th>
                  <th>Detections</th>
                  <th>Mode</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i) => (
                  <tr key={i.id} style={{ cursor: "pointer" }} onClick={() => openDetail(i.id)}>
                    <td>{i.original_filename}</td>
                    <td><StatusBadge status={i.source_type.toUpperCase()} /></td>
                    <td>{i.detection_count}</td>
                    <td className="text-dim">{i.detection_mode.replace(/_/g, " ")}</td>
                    <td className="text-dim">{new Date(i.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="flex gap-8 mt-16">
            <button className="btn btn-sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Previous</button>
            <button className="btn btn-sm" disabled={inspections.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>Next</button>
            <a className="btn btn-sm" href="/api/reports/inspections.csv" target="_blank">Export CSV</a>
          </div>
        </div>

        <div className="card">
          <div className="section-title">Inspection Detail</div>
          {!selected ? (
            <EmptyState title="Select a row to view details" />
          ) : (
            <div>
              <div className="flex gap-8 items-center">
                <StatusBadge status={selected.status.toUpperCase()} />
                <span className="text-dim">{selected.detection_mode.replace(/_/g, " ")}</span>
                <button className="btn btn-sm btn-danger" style={{ marginLeft: "auto" }} onClick={() => remove(selected.id)}>Delete</button>
              </div>
              <div className="grid grid-cols-2 mt-8">
                {selected.original_asset_path && (
                  <div>
                    <div className="text-faint" style={{ fontSize: 11 }}>Original</div>
                    <img src={selected.original_asset_path} style={{ width: "100%", borderRadius: 8 }} />
                  </div>
                )}
                {selected.annotated_asset_path && (
                  <div>
                    <div className="text-faint" style={{ fontSize: 11 }}>Annotated</div>
                    <img src={selected.annotated_asset_path} style={{ width: "100%", borderRadius: 8 }} />
                  </div>
                )}
              </div>
              {selected.error_message && <div className="warning-banner mt-8">{selected.error_message}</div>}
              <div className="mt-16">
                <strong>{selected.detections?.length ?? 0}</strong> detection(s)
              </div>
              {selected.detections && selected.detections.length > 0 && (
                <table className="mt-8">
                  <thead><tr><th>Class</th><th>Confidence</th><th>Field coords</th></tr></thead>
                  <tbody>
                    {selected.detections.map((d) => (
                      <tr key={d.id}>
                        <td>{d.class_name}</td>
                        <td><ConfidenceBar value={d.confidence} /></td>
                        <td className="mono text-dim">{d.field_x !== null ? `${d.field_x.toFixed(2)}, ${d.field_y?.toFixed(2)}` : "—"}</td>
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
