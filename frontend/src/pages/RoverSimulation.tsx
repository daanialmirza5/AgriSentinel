import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { RoverEventT, RoverStatusT, TargetT } from "../types";
import { EmptyState, StatusBadge } from "../components/common";

const VIEW_W = 560;
const VIEW_H = 400;

export default function RoverSimulation() {
  const { selectedField, selectedFieldId } = useFieldContext();
  const [rover, setRover] = useState<RoverStatusT | null>(null);
  const [targets, setTargets] = useState<TargetT[]>([]);
  const [events, setEvents] = useState<RoverEventT[]>([]);
  const [selectedTargetId, setSelectedTargetId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [actuatorMsg, setActuatorMsg] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  async function refresh() {
    if (!selectedFieldId) return;
    const [r, t, ev] = await Promise.all([
      api.get<RoverStatusT>(`/rover/status?field_id=${selectedFieldId}`),
      api.get<TargetT[]>(`/targets?field_id=${selectedFieldId}`),
      api.get<RoverEventT[]>(`/rover/events?field_id=${selectedFieldId}&limit=15`).catch(() => []),
    ]);
    setRover(r);
    setTargets(t);
    setEvents(ev || []);
  }

  useEffect(() => {
    refresh();
    pollRef.current = window.setInterval(refresh, 1000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [selectedFieldId]);

  async function action(fn: () => Promise<any>) {
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }

  if (!selectedFieldId || !selectedField) {
    return <EmptyState title="No field selected" />;
  }

  const scaleX = VIEW_W / Math.max(1, selectedField.width_m);
  const scaleY = VIEW_H / Math.max(1, selectedField.length_m);
  const toPx = (x: number, y: number) => [x * scaleX, y * scaleY];

  const activeTarget = targets.find((t) => t.id === rover?.current_target_id);
  const restricted = selectedField.configuration?.restricted_zones || [];
  const obstacles = selectedField.configuration?.obstacles || [];
  const navigableTargets = targets.filter((t) => ["DETECTED", "REVIEW_REQUIRED", "SELECTED", "PLANNED"].includes(t.status) && t.detection.field_x !== null);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Rover Simulation</h1>
          <p className="page-subtitle">Virtual 2D rover navigating the configured field. No physical rover is connected.</p>
        </div>
      </div>

      {rover?.safety_state === "ESTOP" && <div className="danger-banner">EMERGENCY STOP ENGAGED — reset required before further movement.</div>}
      {error && <div className="danger-banner">{error}</div>}
      {actuatorMsg && <div className="warning-banner">{actuatorMsg}</div>}

      <div className="grid grid-cols-2">
        <div className="card">
          <div className="section-title">Field View</div>
          <svg width="100%" viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} style={{ background: "#0a120e", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
            {restricted.map((z: any, i: number) => {
              const [x1, y1] = toPx(z.x1, z.y1);
              const [x2, y2] = toPx(z.x2, z.y2);
              return <rect key={`r${i}`} x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="rgba(239,87,87,0.15)" stroke="#ef5757" strokeDasharray="4 3" />;
            })}
            {obstacles.map((z: any, i: number) => {
              const [x1, y1] = toPx(z.x1, z.y1);
              const [x2, y2] = toPx(z.x2, z.y2);
              return <rect key={`o${i}`} x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="rgba(159,179,171,0.25)" />;
            })}
            {targets.filter((t) => t.detection.field_x !== null).map((t) => {
              const [x, y] = toPx(t.detection.field_x!, t.detection.field_y!);
              const color = t.status === "COMPLETED" ? "#5fd47a" : t.id === rover?.current_target_id ? "#f0b429" : "#4fa8e8";
              return <circle key={t.id} cx={x} cy={y} r={t.id === selectedTargetId ? 8 : 5} fill={color} stroke="#0a120e" strokeWidth={1} />;
            })}
            {activeTarget?.detection.field_x != null && rover && (
              <line
                x1={toPx(rover.position_x, rover.position_y)[0]}
                y1={toPx(rover.position_x, rover.position_y)[1]}
                x2={toPx(activeTarget.detection.field_x, activeTarget.detection.field_y!)[0]}
                y2={toPx(activeTarget.detection.field_x, activeTarget.detection.field_y!)[1]}
                stroke="#f0b429"
                strokeDasharray="3 3"
              />
            )}
            {rover && (
              <g transform={`translate(${toPx(rover.position_x, rover.position_y)[0]}, ${toPx(rover.position_x, rover.position_y) [1]}) rotate(${rover.heading_deg})`}>
                <polygon points="-8,-6 10,0 -8,6" fill={rover.safety_state === "ESTOP" ? "#ef5757" : "#5fd47a"} />
              </g>
            )}
          </svg>
          <div className="flex gap-8 mt-8 text-dim" style={{ fontSize: 11 }}>
            <span>🟢 rover</span>
            <span>🔵 target</span>
            <span>🟡 active/path</span>
            <span style={{ color: "#ef5757" }}>▨ restricted zone</span>
          </div>
        </div>

        <div className="card">
          <div className="section-title">Rover Status</div>
          <div className="flex-col gap-8">
            <Row k="State" v={<StatusBadge status={rover?.status ?? "NO_SESSION"} />} />
            <Row k="Safety" v={<StatusBadge status={rover?.safety_state ?? "NORMAL"} />} />
            <Row k="Position" v={rover ? `${rover.position_x.toFixed(2)}, ${rover.position_y.toFixed(2)} m` : "—"} />
            <Row k="Heading" v={rover ? `${rover.heading_deg.toFixed(0)}°` : "—"} />
            <Row k="Speed" v={rover ? `${rover.speed_mps.toFixed(2)} m/s` : "—"} />
          </div>

          <div className="section-title mt-16">Controls</div>
          <div className="flex gap-8" style={{ flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => action(() => api.post("/rover/simulation/start", { field_id: selectedFieldId }))}>
              Start
            </button>
            <button className="btn" onClick={() => action(() => api.post(`/rover/simulation/pause?field_id=${selectedFieldId}`))}>Pause</button>
            <button className="btn" onClick={() => action(() => api.post(`/rover/simulation/resume?field_id=${selectedFieldId}`))}>Resume</button>
            <button className="btn" onClick={() => action(() => api.post(`/rover/simulation/stop?field_id=${selectedFieldId}`))}>Stop</button>
            <button className="btn" onClick={() => action(() => api.post(`/rover/return-to-start?field_id=${selectedFieldId}`))}>Return to Start</button>
            <button className="btn btn-danger" onClick={() => action(() => api.post(`/rover/emergency-stop?field_id=${selectedFieldId}`))}>
              EMERGENCY STOP
            </button>
            <button className="btn" onClick={() => action(() => api.post(`/rover/reset?field_id=${selectedFieldId}`))}>Reset Safety Lock</button>
          </div>

          <div className="section-title mt-16">Navigate to Target</div>
          <div className="flex gap-8">
            <select value={selectedTargetId} onChange={(e) => setSelectedTargetId(e.target.value)} style={{ flex: 1 }}>
              <option value="">Select a target...</option>
              {navigableTargets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.detection.target_type} · conf {(t.detection.confidence * 100).toFixed(0)}% · priority {t.priority_score.toFixed(2)}
                </option>
              ))}
            </select>
            <button
              className="btn btn-primary"
              disabled={!selectedTargetId}
              onClick={() => action(() => api.post("/rover/navigate", { target_id: selectedTargetId }))}
            >
              Navigate
            </button>
          </div>

          {rover?.status === "INTERVENTION_PENDING" && rover.current_target_id && (
            <div className="mt-16">
              <button
                className="btn btn-primary w-full"
                onClick={() =>
                  action(async () => {
                    const res: any = await api.post("/actuator/simulate", { target_id: rover.current_target_id, operator_approved: true });
                    setActuatorMsg(res.message);
                  })
                }
              >
                Run Simulated Intervention at Target
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="card mt-16">
        <div className="section-title">Event Log</div>
        {events.length === 0 ? (
          <EmptyState title="No events yet" />
        ) : (
          <table>
            <thead>
              <tr><th>Event</th><th>Payload</th><th>Time</th></tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>{e.event_type.replace(/_/g, " ")}</td>
                  <td className="mono text-dim">{JSON.stringify(e.payload)}</td>
                  <td className="text-dim">{new Date(e.timestamp).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
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
