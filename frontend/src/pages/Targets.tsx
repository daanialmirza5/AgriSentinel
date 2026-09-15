import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { TargetT } from "../types";
import { ConfidenceBar, EmptyState, StatusBadge } from "../components/common";

const STATUS_FILTERS = ["ALL", "DETECTED", "REVIEW_REQUIRED", "SELECTED", "PLANNED", "NAVIGATING", "ARRIVED", "INTERVENTION_PENDING", "COMPLETED", "SKIPPED", "BLOCKED"];

export default function Targets() {
  const { selectedFieldId } = useFieldContext();
  const [targets, setTargets] = useState<TargetT[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    if (!selectedFieldId) return;
    setLoading(true);
    const q = filter === "ALL" ? "" : `&status=${filter}`;
    const t = await api.get<TargetT[]>(`/targets?field_id=${selectedFieldId}${q}`);
    setTargets(t);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, [selectedFieldId, filter]);

  async function doAction(id: string, action: string) {
    await api.post(`/targets/${id}/${action}`);
    refresh();
  }

  if (!selectedFieldId) return <EmptyState title="No field selected" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Targets</h1>
          <p className="page-subtitle">Review, prioritize, and approve detected targets.</p>
        </div>
      </div>

      <div className="flex gap-8 mt-8" style={{ flexWrap: "wrap" }}>
        {STATUS_FILTERS.map((s) => (
          <button key={s} className={`btn btn-sm${filter === s ? " btn-primary" : ""}`} onClick={() => setFilter(s)}>
            {s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="card mt-16">
        {loading ? (
          <div className="text-dim">Loading...</div>
        ) : targets.length === 0 ? (
          <EmptyState icon="🎯" title="No targets match this filter" />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Confidence</th>
                <th>Field coords</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Approved</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => (
                <tr key={t.id}>
                  <td><StatusBadge status={t.detection.target_type} /></td>
                  <td><ConfidenceBar value={t.detection.confidence} /></td>
                  <td className="mono text-dim">
                    {t.detection.field_x !== null ? `${t.detection.field_x.toFixed(2)}, ${t.detection.field_y?.toFixed(2)}` : "—"}
                  </td>
                  <td title={t.priority_explanation}>{t.priority_score.toFixed(2)}</td>
                  <td><StatusBadge status={t.status} /></td>
                  <td>{t.operator_approved ? "Yes" : "No"}</td>
                  <td>
                    <div className="flex gap-8">
                      <button className="btn btn-sm" onClick={() => doAction(t.id, "approve")}>Approve</button>
                      <button className="btn btn-sm" onClick={() => doAction(t.id, "plan")}>Plan</button>
                      <button className="btn btn-sm" onClick={() => doAction(t.id, "skip")}>Skip</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
