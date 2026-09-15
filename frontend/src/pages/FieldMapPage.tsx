import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { RoverStatusT, TargetT } from "../types";
import { ConfidenceBar, EmptyState, StatusBadge } from "../components/common";

const VIEW_W = 640;
const VIEW_H = 440;

export default function FieldMapPage() {
  const { selectedField, selectedFieldId } = useFieldContext();
  const [targets, setTargets] = useState<TargetT[]>([]);
  const [rover, setRover] = useState<RoverStatusT | null>(null);
  const [selected, setSelected] = useState<TargetT | null>(null);

  async function refresh() {
    if (!selectedFieldId) return;
    const [t, r] = await Promise.all([
      api.get<TargetT[]>(`/targets?field_id=${selectedFieldId}`),
      api.get<RoverStatusT>(`/rover/status?field_id=${selectedFieldId}`).catch(() => null),
    ]);
    setTargets(t);
    setRover(r);
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, [selectedFieldId]);

  if (!selectedFieldId || !selectedField) return <EmptyState title="No field selected" />;

  const scaleX = VIEW_W / Math.max(1, selectedField.width_m);
  const scaleY = VIEW_H / Math.max(1, selectedField.length_m);
  const toPx = (x: number, y: number) => [x * scaleX, y * scaleY];
  const rows = Math.max(1, Math.round(selectedField.width_m / Math.max(0.1, selectedField.row_spacing_m)));
  const restricted = selectedField.configuration?.restricted_zones || [];
  const obstacles = selectedField.configuration?.obstacles || [];
  const completed = targets.filter((t) => t.status === "COMPLETED");

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Field Map</h1>
          <p className="page-subtitle">{selectedField.name} — {selectedField.width_m}m × {selectedField.length_m}m, {selectedField.crop_type}</p>
        </div>
      </div>

      <div className="grid grid-cols-2">
        <div className="card">
          <div className="section-title">Field Layout</div>
          <svg width="100%" viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} style={{ background: "#0a120e", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
            {Array.from({ length: rows }).map((_, i) => {
              const x = ((i + 0.5) / rows) * VIEW_W;
              return <line key={i} x1={x} y1={0} x2={x} y2={VIEW_H} stroke="rgba(95,212,122,0.15)" strokeWidth={4} />;
            })}
            {restricted.map((z: any, i: number) => {
              const [x1, y1] = toPx(z.x1, z.y1);
              const [x2, y2] = toPx(z.x2, z.y2);
              return <rect key={`r${i}`} x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="rgba(239,87,87,0.15)" stroke="#ef5757" strokeDasharray="4 3" />;
            })}
            {obstacles.map((z: any, i: number) => {
              const [x1, y1] = toPx(z.x1, z.y1);
              const [x2, y2] = toPx(z.x2, z.y2);
              return <rect key={`o${i}`} x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="rgba(159,179,171,0.3)" />;
            })}
            {targets.filter((t) => t.detection.field_x !== null).map((t) => {
              const [x, y] = toPx(t.detection.field_x!, t.detection.field_y!);
              const color = t.status === "COMPLETED" ? "#5fd47a" : t.status === "BLOCKED" ? "#ef5757" : "#4fa8e8";
              return (
                <circle
                  key={t.id}
                  cx={x}
                  cy={y}
                  r={selected?.id === t.id ? 9 : 6}
                  fill={color}
                  stroke="#0a120e"
                  strokeWidth={2}
                  style={{ cursor: "pointer" }}
                  onClick={() => setSelected(t)}
                />
              );
            })}
            {rover && (
              <circle cx={toPx(rover.position_x, rover.position_y)[0]} cy={toPx(rover.position_x, rover.position_y)[1]} r={7} fill="#f0b429" stroke="#0a120e" strokeWidth={2} />
            )}
          </svg>
          <div className="flex gap-8 mt-8 text-dim" style={{ fontSize: 11 }}>
            <span>🔵 pending target</span>
            <span>🟢 completed</span>
            <span>🔴 blocked</span>
            <span>🟡 rover</span>
          </div>
        </div>

        <div className="card">
          <div className="section-title">Target Details</div>
          {!selected ? (
            <EmptyState icon="🎯" title="Click a marker to inspect a target" />
          ) : (
            <div className="flex-col gap-8">
              <Row k="Type" v={<StatusBadge status={selected.detection.target_type} />} />
              <Row k="Status" v={<StatusBadge status={selected.status} />} />
              <Row k="Confidence" v={<ConfidenceBar value={selected.detection.confidence} />} />
              <Row k="Field coords" v={`${selected.detection.field_x?.toFixed(2)}, ${selected.detection.field_y?.toFixed(2)} m`} />
              <Row k="Localization" v={selected.detection.localization_confidence} />
              <Row k="Priority" v={selected.priority_score.toFixed(3)} />
              <div className="text-dim" style={{ fontSize: 11.5 }}>{selected.priority_explanation}</div>
            </div>
          )}

          <div className="section-title mt-16">Completed Interventions</div>
          {completed.length === 0 ? (
            <div className="text-dim">None yet.</div>
          ) : (
            <ul>
              {completed.map((t) => (
                <li key={t.id} className="text-dim">
                  {t.detection.target_type} at {t.detection.field_x?.toFixed(1)}, {t.detection.field_y?.toFixed(1)}m — {t.completed_at ? new Date(t.completed_at).toLocaleString() : ""}
                </li>
              ))}
            </ul>
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
      <span>{v}</span>
    </div>
  );
}
