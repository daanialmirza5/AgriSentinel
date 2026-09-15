import { ReactNode } from "react";

export function StatCard({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="card stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {sub && <span className="stat-sub">{sub}</span>}
    </div>
  );
}

const BADGE_MAP: Record<string, string> = {
  DETECTED: "badge-blue",
  REVIEW_REQUIRED: "badge-amber",
  SELECTED: "badge-blue",
  PLANNED: "badge-blue",
  NAVIGATING: "badge-amber",
  ARRIVED: "badge-amber",
  INTERVENTION_PENDING: "badge-amber",
  INTERVENTING: "badge-amber",
  COMPLETED: "badge-green",
  SKIPPED: "badge-gray",
  BLOCKED: "badge-red",
  INVALID: "badge-red",
  IDLE: "badge-gray",
  READY: "badge-blue",
  PAUSED: "badge-amber",
  STOPPED: "badge-gray",
  SAFETY_LOCK: "badge-red",
  ERROR: "badge-red",
  NO_SESSION: "badge-gray",
  weed: "badge-red",
  crop: "badge-green",
  unclassified_vegetation: "badge-amber",
  generic_object: "badge-blue",
  unclassified: "badge-gray",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = BADGE_MAP[status] || "badge-gray";
  return <span className={`badge ${cls}`}>{status.replace(/_/g, " ")}</span>;
}

export function EmptyState({ icon = "📭", title, hint }: { icon?: string; title: string; hint?: string }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <div>{title}</div>
      {hint && <div className="stat-sub mt-8">{hint}</div>}
    </div>
  );
}

export function Loading({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-8 text-dim">
      <span className="loading-spinner" /> {label}
    </div>
  );
}

export function WarningBanner({ children }: { children: ReactNode }) {
  return <div className="warning-banner">⚠️ <div>{children}</div></div>;
}

export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "var(--accent)" : pct >= 40 ? "var(--warn)" : "var(--danger)";
  return (
    <div className="flex items-center gap-8">
      <div style={{ width: 60, height: 6, background: "var(--border)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color }} />
      </div>
      <span className="mono text-dim">{pct}%</span>
    </div>
  );
}
