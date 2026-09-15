import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useFieldContext } from "../state/FieldContext";
import { EmptyState, Loading, WarningBanner } from "../components/common";

interface CameraStatus {
  active: boolean;
  device_index: number | null;
  available: boolean;
  frames_processed: number;
  last_detection_count: number;
  error: string | null;
}

export default function LiveMonitoring() {
  const { selectedFieldId } = useFieldContext();
  const [devices, setDevices] = useState<number[]>([]);
  const [deviceIndex, setDeviceIndex] = useState(0);
  const [status, setStatus] = useState<CameraStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamKey, setStreamKey] = useState(0);

  async function refreshDevices() {
    try {
      const res = await api.get<{ devices: number[] }>("/camera/devices");
      setDevices(res.devices);
    } catch {
      setDevices([]);
    }
  }

  async function refreshStatus() {
    const s = await api.get<CameraStatus>("/camera/status");
    setStatus(s);
    return s;
  }

  useEffect(() => {
    refreshDevices();
    refreshStatus();
    const t = setInterval(refreshStatus, 2000);
    return () => clearInterval(t);
  }, []);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const s = await api.post<CameraStatus>("/camera/start", { device_index: deviceIndex, field_id: selectedFieldId });
      setStatus(s);
      if (!s.active) setError(s.error || "Camera could not be started.");
      setStreamKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function stop() {
    setBusy(true);
    try {
      const s = await api.post<CameraStatus>("/camera/stop");
      setStatus(s);
    } finally {
      setBusy(false);
    }
  }

  async function capture() {
    if (!selectedFieldId) return;
    setBusy(true);
    setError(null);
    try {
      await api.post(`/camera/capture?field_id=${selectedFieldId}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!selectedFieldId) {
    return <EmptyState title="No field selected" />;
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Monitoring</h1>
          <p className="page-subtitle">Local webcam capture via OpenCV, with detection overlay.</p>
        </div>
      </div>

      <WarningBanner>
        If no physical camera is attached to this machine, live monitoring will report an error here — the
        rest of the application (Vision Lab image/video upload) remains fully usable without a camera.
      </WarningBanner>

      <div className="grid grid-cols-2">
        <div className="card">
          <div className="section-title">Camera Control</div>
          <div className="flex gap-8 items-center">
            <label style={{ marginBottom: 0 }}>Device</label>
            <select value={deviceIndex} onChange={(e) => setDeviceIndex(Number(e.target.value))}>
              {(devices.length ? devices : [0, 1, 2]).map((d) => (
                <option key={d} value={d}>
                  Camera {d}
                </option>
              ))}
            </select>
            <button className="btn btn-sm" onClick={refreshDevices}>Rescan</button>
          </div>
          <div className="flex gap-8 mt-16">
            <button className="btn btn-primary" disabled={busy || status?.active} onClick={start}>
              Start Camera
            </button>
            <button className="btn btn-danger" disabled={busy || !status?.active} onClick={stop}>
              Stop Camera
            </button>
            <button className="btn" disabled={busy || !status?.active} onClick={capture}>
              Capture &amp; Save Inspection
            </button>
          </div>
          {error && <div className="danger-banner mt-16">{error}</div>}
          {status && (
            <div className="mt-16 flex-col gap-8">
              <div className="flex justify-between"><span className="text-dim">Active</span><span>{String(status.active)}</span></div>
              <div className="flex justify-between"><span className="text-dim">Frames processed</span><span>{status.frames_processed}</span></div>
              <div className="flex justify-between"><span className="text-dim">Last detection count</span><span>{status.last_detection_count}</span></div>
              {status.error && <div className="flex justify-between"><span className="text-dim">Error</span><span>{status.error}</span></div>}
            </div>
          )}
        </div>

        <div className="card">
          <div className="section-title">Live Preview</div>
          {status?.active ? (
            <img key={streamKey} src="/api/camera/stream" style={{ width: "100%", borderRadius: 8, background: "#000" }} />
          ) : (
            <EmptyState icon="📷" title="Camera not active" hint="Start the camera to see a live detection overlay." />
          )}
        </div>
      </div>
    </div>
  );
}
