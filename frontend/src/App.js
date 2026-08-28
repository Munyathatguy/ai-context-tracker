import { useEffect, useState } from "react";
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

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [latestId, setLatestId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);

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
          {s && (
            <div className="text-right text-xs text-[#888888]" data-testid="session-meta">
              session <span className="text-white">{s.session_id}</span>
              <div>{detail.model_spec.id} · {detail.model_spec.provider}</div>
            </div>
          )}
        </header>

        {error && (
          <div className="m-6 border border-[#FF3B30] p-4 text-[#FF3B30] text-sm" data-testid="api-error">{error}</div>
        )}

        {!s && !error && (
          <div className="m-6 border border-[#222222] p-8 text-[#888888] text-sm" data-testid="empty-state">
            No sessions recorded yet. Run the MCP server and record usage, or seed demo data.
          </div>
        )}

        {s && (
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
    </div>
  );
}
