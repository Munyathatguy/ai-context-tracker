import { CurrencyDollar, ArrowsClockwise, Timer, Cpu } from "@phosphor-icons/react";

const Metric = ({ icon: Icon, label, value, accent, testId }) => (
  <div className="border border-[#222222] bg-[#111111] p-4 flex-1" data-testid={testId}>
    <div className="flex items-center gap-2 text-[#888888] text-[10px] uppercase tracking-widest">
      <Icon size={12} weight="duotone" /> {label}
    </div>
    <div className={`mt-2 text-2xl font-bold tracking-tighter ${accent || "text-white"}`}>{value}</div>
  </div>
);

const fmtClock = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "—");

const elapsed = (start) => {
  if (!start) return "—";
  const s = Math.max(0, (Date.now() - new Date(start).getTime()) / 1000);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
};

const gap = (iso) => {
  if (!iso) return "—";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)} sec ago`;
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  return `${Math.floor(s / 3600)} hr ago`;
};

export const MetricRow = ({ session, detail }) => (
  <div className="md:col-span-12 flex flex-col sm:flex-row gap-4" data-testid="metric-row">
    <Metric icon={ArrowsClockwise} label="Turn" value={session.turn} testId="metric-turn" />
    <Metric icon={CurrencyDollar} label="Session Cost" value={`$${(session.cost_usd || 0).toFixed(4)}`} accent="text-[#00FF00]" testId="metric-cost" />
    <Metric icon={Timer} label="Elapsed" value={elapsed(session.started_at)} testId="metric-elapsed" />
    <Metric icon={Cpu} label="Context Left" value={`${detail.pct_remaining.toFixed(1)}%`}
      accent={detail.pct_remaining > 30 ? "text-[#00FF00]" : detail.pct_remaining > 15 ? "text-[#FFD700]" : "text-[#FF3B30]"}
      testId="metric-remaining" />
  </div>
);

export const ModelCard = ({ spec }) => (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="model-card">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">Model Awareness</h2>
    <div className="text-lg font-bold text-[#00BFFF] tracking-tighter">{spec.id}</div>
    <div className="text-[10px] text-[#888888] uppercase">{spec.provider}</div>
    <div className="mt-3 space-y-1 text-xs">
      <div className="flex justify-between"><span className="text-[#888888]">context window</span><span>{spec.context_window.toLocaleString()}</span></div>
      <div className="flex justify-between"><span className="text-[#888888]">max output</span><span>{spec.max_output.toLocaleString()}</span></div>
      <div className="flex justify-between"><span className="text-[#888888]">pricing /1M</span><span>${spec.price_in} in · ${spec.price_out} out</span></div>
    </div>
    <div className="mt-3 flex flex-wrap gap-1">
      {spec.capabilities.map((c) => (
        <span key={c} className="text-[9px] uppercase border border-[#333333] text-[#aaaaaa] px-1.5 py-0.5">{c.replace("_", " ")}</span>
      ))}
    </div>
  </section>
);

export const TimelineCard = ({ session }) => (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="timeline-card">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">Time Awareness</h2>
    <div className="space-y-2 text-xs">
      <div className="flex justify-between"><span className="text-[#888888]">current time</span><span data-testid="current-time">{new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span></div>
      <div className="flex justify-between"><span className="text-[#888888]">session started</span><span>{fmtClock(session.started_at)}</span></div>
      <div className="flex justify-between"><span className="text-[#888888]">last message</span><span data-testid="last-message-gap">{gap(session.last_message_at)}</span></div>
      <div className="flex justify-between"><span className="text-[#888888]">models used</span><span>{(session.model_history || []).filter(Boolean).join(" → ") || session.model}</span></div>
    </div>
  </section>
);
