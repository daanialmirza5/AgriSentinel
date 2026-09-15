import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { AnalyticsSummaryT, ModelStatusT, RoverStatusT, RoverEventT } from "../types";
import { StatCard, StatusBadge, EmptyState, Loading, WarningBanner } from "../components/common";

export default function Overview() {
  const { selectedField, selectedFieldId, fields } = useFieldContext();
  const [summary, setSummary] = useState<AnalyticsSummaryT | null>(null);
  const [model, setModel] = useState<ModelStatusT | null>(null);
  const [rover, setRover] = useState<RoverStatusT | null>(null);
  const [events, setEvents] = useState<RoverEventT[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const [m] = await Promise.all([api.get<ModelStatusT>("/model/status")]);
      if (cancelled) return;
      setModel(m);
      if (selectedFieldId) {
        const [s, r, ev] = await Promise.all([
          api.get<AnalyticsSummaryT>(`/analytics/summary?field_id=${selectedFieldId}`),
          api.get<RoverStatusT>(`/rover/status?field_id=${selectedFieldId}`).catch(() => null),
          api.get<RoverEventT[]>(`/rover/events?field_id=${selectedFieldId}&limit=8`).catch(() => []),
        ]);
        if (cancelled) return;
        setSummary(s);
        setRover(r);
        setEvents(ev || []);
      } else {
        setSummary(null);
      }
      setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [selectedFieldId]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">See the field. Find the weeds. Protect the crop.</p>
        </div>
      </div>

      {model?.warning && <WarningBanner>{model.warning}</WarningBanner>}

      {fields.length === 0 && (
        <div className="card">
          <EmptyState icon="🌱" title="No fields configured yet" hint="Create your first field in Settings to start inspecting images." />
          <div className="flex" style={{ justifyContent: "center" }}>
            <Link to="/settings" className="btn btn-primary">
              Go to Settings
            </Link>
          </div>
        </div>
      )}

      {fields.length > 0 && loading && <Loading label="Loading dashboard..." />}

      {fields.length > 0 && !loading && (
        <>
          <div className="grid grid-cols-4 mt-16">
            <StatCard label="Monitoring Status" value={<StatusBadge status={rover?.status ?? "NO_SESSION"} />} sub={selectedField?.name} />
            <StatCard
              label="Model Status"
              value={model?.loaded ? (model.is_generic_demo ? "Generic demo" : "Custom model") : "Unavailable"}
              sub={model?.label}
            />
            <StatCard label="Total Inspections" value={summary?.total_inspections ?? 0} />
            <StatCard label="Detected Targets" value={summary?.total_targets ?? 0} sub={`${summary?.pending_targets ?? 0} pending`} />
          </div>
          <div className="grid grid-cols-4 mt-16">
            <StatCard label="Completed Interventions" value={summary?.completed_interventions ?? 0} />
            <StatCard label="Rover Status" value={<StatusBadge status={rover?.status ?? "NO_SESSION"} />} sub={rover?.safety_state} />
            <StatCard label="Avg Inference Time" value={summary?.average_inference_time_ms ? `${summary.average_inference_time_ms.toFixed(0)} ms` : "—"} />
            <StatCard label="Last Inspection" value={summary?.last_inspection_at ? new Date(summary.last_inspection_at).toLocaleString() : "—"} />
          </div>

          <div className="grid grid-cols-2 mt-16">
            <div className="card">
              <div className="section-title">Field Overview</div>
              {selectedField ? (
                <div className="flex-col gap-8">
                  <Row k="Name" v={selectedField.name} />
                  <Row k="Crop type" v={selectedField.crop_type} />
                  <Row k="Dimensions" v={`${selectedField.width_m} m × ${selectedField.length_m} m`} />
                  <Row k="Row spacing" v={`${selectedField.row_spacing_m} m`} />
                  <Row k="Detections" v={summary?.total_detections ?? 0} />
                  <Row k="Targets" v={summary?.total_targets ?? 0} />
                  {selectedField.configuration?.is_demo && <span className="badge badge-amber">DEMO FIELD</span>}
                </div>
              ) : (
                <EmptyState title="No field selected" />
              )}
            </div>

            <div className="card">
              <div className="section-title">Detection Summary</div>
              {summary && Object.keys(summary.detections_by_target_type).length > 0 ? (
                <div className="flex-col gap-8">
                  {Object.entries(summary.detections_by_target_type).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <StatusBadge status={type} />
                      <span className="mono">{count}</span>
                    </div>
                  ))}
                  <div className="flex justify-between mt-8">
                    <span className="text-dim">Average confidence</span>
                    <span className="mono">{summary.average_confidence ? `${Math.round(summary.average_confidence * 100)}%` : "—"}</span>
                  </div>
                </div>
              ) : (
                <EmptyState icon="📊" title="No detections yet" hint="Run an inspection in the Vision Lab to populate this." />
              )}
            </div>
          </div>

          <div className="card mt-16">
            <div className="section-title">Recent Activity</div>
            {events.length === 0 ? (
              <EmptyState icon="🕓" title="No recent rover activity" hint="Start a rover simulation to see events here." />
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Details</th>
                    <th>Time</th>
                  </tr>
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

          <div className="flex gap-12 mt-16">
            <Link to="/vision-lab" className="btn btn-primary">Run Inspection</Link>
            <Link to="/rover" className="btn">Open Rover Simulation</Link>
            <Link to="/map" className="btn">View Field Map</Link>
          </div>
        </>
      )}
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
