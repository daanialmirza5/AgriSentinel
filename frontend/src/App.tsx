import { NavLink, Route, Routes } from "react-router-dom";
import { useFieldContext } from "./state/FieldContext";
import Overview from "./pages/Overview";
import VisionLab from "./pages/VisionLab";
import LiveMonitoring from "./pages/LiveMonitoring";
import RoverSimulation from "./pages/RoverSimulation";
import FieldMapPage from "./pages/FieldMapPage";
import Targets from "./pages/Targets";
import History from "./pages/History";
import AnalyticsPage from "./pages/AnalyticsPage";
import SettingsPage from "./pages/SettingsPage";

const NAV = [
  { to: "/", label: "Overview", icon: "▤" },
  { to: "/vision-lab", label: "Vision Lab", icon: "◉" },
  { to: "/live", label: "Live Monitoring", icon: "●" },
  { to: "/rover", label: "Rover Simulation", icon: "▶" },
  { to: "/map", label: "Field Map", icon: "▦" },
  { to: "/targets", label: "Targets", icon: "⌖" },
  { to: "/history", label: "Inspection History", icon: "⧖" },
  { to: "/analytics", label: "Analytics", icon: "▨" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

function FieldSelector() {
  const { fields, selectedFieldId, setSelectedFieldId, loading } = useFieldContext();
  if (loading) return null;
  if (fields.length === 0) {
    return <div className="stat-sub">No fields yet — create one in Settings.</div>;
  }
  return (
    <select className="field-select" value={selectedFieldId ?? ""} onChange={(e) => setSelectedFieldId(e.target.value)}>
      {fields.map((f) => (
        <option key={f.id} value={f.id}>
          {f.name}
        </option>
      ))}
    </select>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AS</div>
          <div>
            <div className="brand-name">AgriSentinel</div>
            <div className="brand-tag">Precision-Ag Rover</div>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <FieldSelector />
        </div>
        <nav>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          Simulation-first platform.
          <br />
          No physical hardware connected.
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/vision-lab" element={<VisionLab />} />
          <Route path="/live" element={<LiveMonitoring />} />
          <Route path="/rover" element={<RoverSimulation />} />
          <Route path="/map" element={<FieldMapPage />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/history" element={<History />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
