import { useState } from "react";
import { Warning, CheckSquare, Square, CircleHalf, FileText } from "@phosphor-icons/react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";

const LEVEL = {
  warn: { color: "#FFD700", label: "WARN" },
  danger: { color: "#FF9500", label: "DANGER" },
  red: { color: "#FF3B30", label: "RED ALERT" },
};

export const AlertsPanel = ({ alerts = [], rateLimits }) => (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="alerts-panel">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">Alerts & Rate Limit</h2>
    {rateLimits?.limit_tokens ? (
      <div className="mb-3 border border-[#222222] p-2" data-testid="rate-limit-watch">
        <div className="flex justify-between text-[10px] uppercase tracking-widest">
          <span className="text-[#888888]">rate limit headroom</span>
          <span className="text-white" data-testid="rate-limit-pct">{rateLimits.pct_remaining}%</span>
        </div>
        <div className="h-1.5 bg-[#1c1c1c] mt-1.5">
          <div className="h-full transition-[width] duration-500" style={{
            width: `${rateLimits.pct_remaining}%`,
            backgroundColor: rateLimits.pct_remaining > 30 ? "#00FF00" : rateLimits.pct_remaining > 10 ? "#FFD700" : "#FF3B30",
          }} />
        </div>
        <div className="text-[10px] text-[#666666] mt-1">
          {(rateLimits.remaining_tokens || 0).toLocaleString()} / {(rateLimits.limit_tokens || 0).toLocaleString()} tokens available
        </div>
      </div>
    ) : (
      <div className="mb-3 text-[10px] text-[#666666]" data-testid="rate-limit-empty">rate limit headroom: no data yet</div>
    )}
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

const HSection = ({ title, text }) => (
  <div>
    <div className="text-[10px] uppercase tracking-widest text-[#00BFFF] mb-1">{title}</div>
    <p className="text-xs text-[#cccccc] whitespace-pre-wrap leading-relaxed">{text || "n/a"}</p>
  </div>
);

export const HandoffsPanel = ({ handoffs = [], summaries = [] }) => {
  const [sel, setSel] = useState(null);
  return (
  <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="handoffs-panel">
    <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">
      Continuity — Handoffs & Recent Activity
    </h2>
    <div className="space-y-2 max-h-56 overflow-y-auto">
      {handoffs.map((h, i) => (
        <button key={i} onClick={() => setSel(h)} data-testid={`handoff-${i}`}
          className="w-full text-left border border-[#00BFFF] p-2 hover:bg-[#0d1b22] transition-colors">
          <div className="flex items-center justify-between text-[10px] font-bold text-[#00BFFF]">
            <span className="flex items-center gap-2"><FileText size={12} weight="duotone" /> HANDOFF {h.auto ? "(AUTO)" : ""} · turn {h.turn}</span>
            <span className="text-[#888888] font-normal">click to read →</span>
          </div>
          <p className="text-[11px] text-[#cccccc] mt-1 truncate"><span className="text-[#888888]">goals:</span> {h.goals}</p>
          <p className="text-[11px] text-[#cccccc] truncate"><span className="text-[#888888]">remaining:</span> {h.remaining_tasks}</p>
        </button>
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
    <Dialog open={!!sel} onOpenChange={(o) => !o && setSel(null)}>
      <DialogContent className="bg-[#111111] border border-[#333333] rounded-none text-white font-mono max-w-lg max-h-[80vh] overflow-y-auto" data-testid="handoff-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading uppercase tracking-tight text-sm text-[#00BFFF]">
            Session Handoff {sel?.auto ? "(auto-generated)" : ""}
          </DialogTitle>
        </DialogHeader>
        {sel && (
          <div className="space-y-4">
            <div className="text-[10px] text-[#888888] border-b border-[#222222] pb-2">
              {sel.created_at?.slice(0, 19).replace("T", " ")} UTC · model {sel.model} · turn {sel.turn} ·{" "}
              {(sel.usage?.total || 0).toLocaleString()} tokens · ${sel.cost_usd}
            </div>
            <HSection title="Goals" text={sel.goals} />
            <HSection title="Progress" text={sel.progress} />
            <HSection title="Remaining Tasks" text={sel.remaining_tasks} />
            <HSection title="Key Decisions" text={sel.key_decisions} />
            {sel.tasks?.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-widest text-[#00BFFF] mb-1">Task snapshot</div>
                {sel.tasks.map((t) => (
                  <div key={t.id} className="text-xs text-[#cccccc]">[{t.status}] {t.title}</div>
                ))}
              </div>
            )}
            <p className="text-[10px] text-[#555555]">Also saved to disk as JSON + markdown under ~/.ai-context-tracker/handoffs/</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  </section>
  );
};
