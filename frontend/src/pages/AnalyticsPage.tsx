import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { AnalyticsSummaryT } from "../types";
import { EmptyState, StatCard } from "../components/common";

export default function AnalyticsPage() {
  const { selectedFieldId } = useFieldContext();
  const [summary, setSummary] = useState<AnalyticsSummaryT | null>(null);
  const [byDate, setByDate] = useState<{ date: string; count: number }[]>([]);

  useEffect(() => {
    if (!selectedFieldId) return;
    api.get<AnalyticsSummaryT>(`/analytics/summary?field_id=${selectedFieldId}`).then(setSummary);
    api.get<{ by_date: any[] }>(`/analytics/detections?field_id=${selectedFieldId}`).then((r) => setByDate(r.by_date));
  }, [selectedFieldId]);

  if (!selectedFieldId) return <EmptyState title="No field selected" />;
  if (!summary) return null;

  const typeData = Object.entries(summary.detections_by_target_type).map(([type, count]) => ({ type, count }));
  const statusData = Object.entries(summary.target_status_distribution).map(([status, count]) => ({ status, count }));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">Statistics computed directly from stored inspection records. Estimates are based on sampled imagery, not full-field coverage.</p>
        </div>
      </div>

      <div className="grid grid-cols-4">
        <StatCard label="Total Inspections" value={summary.total_inspections} />
        <StatCard label="Total Detections" value={summary.total_detections} />
        <StatCard label="Avg Confidence" value={summary.average_confidence ? `${Math.round(summary.average_confidence * 100)}%` : "—"} />
        <StatCard label="Avg Inference Time" value={summary.average_inference_time_ms ? `${summary.average_inference_time_ms.toFixed(0)} ms` : "—"} />
      </div>

      <div className="grid grid-cols-2 mt-16">
        <div className="card">
          <div className="section-title">Detections by Type</div>
          {typeData.length === 0 ? (
            <EmptyState title="No detections yet" />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={typeData}>
                <CartesianGrid stroke="#253630" strokeDasharray="3 3" />
                <XAxis dataKey="type" stroke="#6b8078" fontSize={11} />
                <YAxis stroke="#6b8078" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#182420", border: "1px solid #253630" }} />
                <Bar dataKey="count" fill="#5fd47a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="card">
          <div className="section-title">Target Status Distribution</div>
          {statusData.length === 0 ? (
            <EmptyState title="No targets yet" />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={statusData}>
                <CartesianGrid stroke="#253630" strokeDasharray="3 3" />
                <XAxis dataKey="status" stroke="#6b8078" fontSize={10} />
                <YAxis stroke="#6b8078" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#182420", border: "1px solid #253630" }} />
                <Bar dataKey="count" fill="#4fa8e8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card mt-16">
        <div className="section-title">Detections Over Time</div>
        {byDate.length === 0 ? (
          <EmptyState title="No time-series data yet" />
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={byDate}>
              <CartesianGrid stroke="#253630" strokeDasharray="3 3" />
              <XAxis dataKey="date" stroke="#6b8078" fontSize={11} />
              <YAxis stroke="#6b8078" fontSize={11} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#182420", border: "1px solid #253630" }} />
              <Line type="monotone" dataKey="count" stroke="#f0b429" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
