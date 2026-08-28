import { useEffect, useRef, useState } from "react";
import "@/App.css";
import "@fontsource/chivo/400.css";
import "@fontsource/chivo/700.css";
import "@fontsource/chivo/900.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "@fontsource/jetbrains-mono/700.css";
import { Sidebar } from "./components/dashboard/Sidebar";
import { ContextGauge } from "./components/dashboard/ContextGauge";
import { TokenBreakdown } from "./components/dashboard/TokenBreakdown";
import { MetricRow, ModelCard, TimelineCard } from "./components/dashboard/Panels";
import { AlertsPanel, TasksPanel, HandoffsPanel } from "./components/dashboard/Activity";
import { SettingsDialog } from "./components/dashboard/SettingsDialog";
import { CompareView } from "./components/dashboard/CompareView";
import { Toaster } from "./components/ui/sonner";
import { ArrowsLeftRight, SpeakerHigh, SpeakerSlash } from "@phosphor-icons/react";

const playChime = () => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [880, 587].forEach((f, i) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = f;
      o.connect(g);
      g.connect(ctx.destination);
      const t = ctx.currentTime + i * 0.18;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.15, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
      o.start(t);
      o.stop(t + 0.65);
    });
  } catch (e) {}
};

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [latestId, setLatestId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [muted, setMuted] = useState(() => localStorage.getItem("act-muted") === "1");
  const alertsRef = useRef({ sid: null, count: 0 });

  useEffect(() => {
    if (!detail?.session) return;
    const { session_id, active_alerts = [] } = detail.session;
    const prev = alertsRef.current;
    if (prev.sid === session_id && active_alerts.length > prev.count && !muted) {
      const fresh = active_alerts.slice(prev.count);
      if (fresh.some((a) => a.level === "danger" || a.level === "red")) playChime();
    }
    alertsRef.current = { sid: session_id, count: active_alerts.length };
  }, [detail, muted]);

  const toggleMute = () => {
    const next = !muted;
    setMuted(next);
    localStorage.setItem("act-muted", next ? "1" : "0");
  };

  useEffect(() => {
    const url = `${API}/tracker/stream${selectedId ? `?session_id=${selectedId}` : ""}`;
    const es = new EventSource(url);
    es.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      setSessions(data.sessions);
      setLatestId(data.latest_session_id);
      setSelectedId((cur) => cur || data.latest_session_id || data.sessions[0]?.session_id || null);
      if (data.detail) setDetail(data.detail);
      setError(null);
    };
    es.onerror = () => setError("Live stream interrupted — reconnecting…");
    return () => es.close();
  }, [selectedId]);

  const s = detail?.session;

  return (
    <div className="h-screen w-full flex overflow-hidden bg-[#0A0A0A] text-white font-mono scanlines" data-testid="app-root">
      <Sidebar sessions={sessions} selectedId={selectedId} latestId={latestId} onSelect={setSelectedId} />
      <main className="flex-1 overflow-y-auto">
        <header className="border-b border-[#222222] px-6 py-4 flex items-center justify-between sticky top-0 bg-[#0A0A0A] z-10">
          <div>
            <h1 className="font-heading text-xl font-black tracking-tight uppercase" data-testid="app-title">
              AI Context Tracker <span className="text-[#00FF00]">▮</span>
            </h1>
            <p className="text-xs text-[#888888]">MCP server companion — live session telemetry</p>
          </div>
          <div className="flex items-center gap-3">
            <button data-testid="compare-toggle-btn" onClick={() => setCompareMode((v) => !v)}
              title="Compare sessions side by side"
              className={`border p-1.5 transition-colors ${compareMode ? "border-[#00FF00] text-[#00FF00]" : "border-[#333333] text-[#888888] hover:text-white hover:border-[#00BFFF]"}`}>
              <ArrowsLeftRight size={16} weight="duotone" />
            </button>
            <button data-testid="sound-toggle-btn" onClick={toggleMute}
              title={muted ? "Unmute alert chime" : "Mute alert chime"}
              className="border border-[#333333] p-1.5 text-[#888888] hover:text-white hover:border-[#00BFFF] transition-colors">
              {muted ? <SpeakerSlash size={16} weight="duotone" /> : <SpeakerHigh size={16} weight="duotone" className="text-[#00FF00]" />}
            </button>
            <SettingsDialog />
            {s && (
              <div className="text-right text-xs text-[#888888]" data-testid="session-meta">
                session <span className="text-white">{s.session_id}</span>
                <div>{detail.model_spec.id} · {detail.model_spec.provider}</div>
              </div>
            )}
          </div>
        </header>

        {error && (
          <div className="m-6 border border-[#FF3B30] p-4 text-[#FF3B30] text-sm" data-testid="api-error">{error}</div>
        )}

        {!s && !error && (
          <div className="m-6 border border-[#222222] p-8 text-[#888888] text-sm" data-testid="empty-state">
            No sessions recorded yet. Run the MCP server and record usage, or seed demo data.
          </div>
        )}

        {compareMode && sessions.length > 0 && <CompareView sessions={sessions} />}

        {!compareMode && s && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 p-6">
            <MetricRow session={s} detail={detail} />
            <div className="md:col-span-4"><ContextGauge detail={detail} /></div>
            <div className="md:col-span-8"><TokenBreakdown usage={s.usage} /></div>
            <div className="md:col-span-4"><ModelCard spec={detail.model_spec} /></div>
            <div className="md:col-span-4"><TimelineCard session={s} /></div>
            <div className="md:col-span-4"><AlertsPanel alerts={s.active_alerts} rateLimits={s.rate_limits} /></div>
            <div className="md:col-span-6"><TasksPanel tasks={s.tasks} /></div>
            <div className="md:col-span-6"><HandoffsPanel handoffs={s.handoffs} summaries={s.message_summaries} /></div>
          </div>
        )}
      </main>
      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}
