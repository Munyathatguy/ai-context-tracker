import { Warning, CheckSquare, Square, CircleHalf, FileText } from "@phosphor-icons/react";

const LEVEL = {
  warn: { color: "#FFD700", label: "WARN" },
  danger: { color: "#FF9500", label: "DANGER" },
  red: { color: "#FF3B30", label: "RED ALERT" },
};

export const AlertsPanel = ({ alerts = [] }) => (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="alerts-panel">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">Alerts</h2>
    {alerts.length === 0 && <div className="text-xs text-[#666666]" data-testid="no-alerts">no active alerts</div>}
    <div className="space-y-2 max-h-48 overflow-y-auto">
      {[...alerts].reverse().map((a, i) => {
        const lv = LEVEL[a.level] || LEVEL.warn;
        return (
          <div key={i} className="border p-2 fade-in" style={{ borderColor: lv.color }} data-testid={`alert-${a.level}`}>
            <div className="flex items-center gap-2 text-[10px] font-bold" style={{ color: lv.color }}>
              <Warning size={12} weight="fill" /> {lv.label} · ≤{a.threshold}% remaining
            </div>
            <p className="text-[11px] text-[#cccccc] mt-1 leading-snug">{a.message}</p>
          </div>
        );
      })}
    </div>
  </section>
);

const ICONS = {
  done: <CheckSquare size={14} className="text-[#00FF00]" weight="fill" />,
  in_progress: <CircleHalf size={14} className="text-[#FFD700]" weight="fill" />,
  todo: <Square size={14} className="text-[#555555]" />,
};

export const TasksPanel = ({ tasks = [] }) => {
  const done = tasks.filter((t) => t.status === "done").length;
  return (
    <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="tasks-panel">
      <div className="flex justify-between items-center mb-3">
        <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888]">Task Checklist</h2>
        <span className="text-xs text-[#00FF00]" data-testid="tasks-progress">{done}/{tasks.length}</span>
      </div>
      {tasks.length === 0 && <div className="text-xs text-[#666666]">no tasks registered</div>}
      <ul className="space-y-2">
        {tasks.map((t) => (
          <li key={t.id} className="flex items-start gap-2 text-xs" data-testid={`task-${t.id}`}>
            {ICONS[t.status] || ICONS.todo}
            <span className={t.status === "done" ? "text-[#666666] line-through" : "text-white"}>{t.title}</span>
          </li>
        ))}
      </ul>
    </section>
  );
};

export const HandoffsPanel = ({ handoffs = [], summaries = [] }) => (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="handoffs-panel">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">
      Continuity — Handoffs & Recent Activity
    </h2>
    <div className="space-y-2 max-h-56 overflow-y-auto">
      {handoffs.map((h, i) => (
        <div key={i} className="border border-[#00BFFF] p-2" data-testid={`handoff-${i}`}>
          <div className="flex items-center gap-2 text-[10px] font-bold text-[#00BFFF]">
            <FileText size={12} weight="duotone" /> HANDOFF {h.auto ? "(AUTO)" : ""} · turn {h.turn}
          </div>
          <p className="text-[11px] text-[#cccccc] mt-1"><span className="text-[#888888]">goals:</span> {h.goals}</p>
          <p className="text-[11px] text-[#cccccc]"><span className="text-[#888888]">remaining:</span> {h.remaining_tasks}</p>
        </div>
      ))}
      {summaries.length > 0 && (
        <div className="pt-2 border-t border-[#222222]">
          <div className="text-[10px] text-[#888888] uppercase mb-1">last 3 message summaries</div>
          {summaries.map((s, i) => (
            <div key={i} className="text-[11px] text-[#aaaaaa] py-0.5" data-testid={`summary-${i}`}>› {s.text}</div>
          ))}
        </div>
      )}
      {handoffs.length === 0 && summaries.length === 0 && <div className="text-xs text-[#666666]">nothing saved yet</div>}
    </div>
  </section>
);
