import { Cpu, Clock } from "@phosphor-icons/react";

const relTime = (iso) => {
  if (!iso) return "";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export const Sidebar = ({ sessions, selectedId, latestId, onSelect }) => (
  <aside className="w-72 shrink-0 border-r border-[#222222] bg-[#111111] flex flex-col" data-testid="sessions-sidebar">
    <div className="px-4 py-4 border-b border-[#222222]">
      <div className="text-xs uppercase tracking-widest text-[#888888] font-heading font-bold">Sessions</div>
      <div className="text-[10px] text-[#555555] mt-1">~/.ai-context-tracker/sessions</div>
    </div>
    <div className="flex-1 overflow-y-auto">
      {sessions.map((s) => {
        const active = s.session_id === selectedId;
        return (
          <button
            key={s.session_id}
            data-testid={`session-item-${s.session_id}`}
            onClick={() => onSelect(s.session_id)}
            className={`w-full text-left px-4 py-3 border-b border-[#1a1a1a] transition-colors ${
              active ? "bg-[#0A0A0A] border-l-2 border-l-[#00FF00]" : "hover:bg-[#161616]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`text-xs ${active ? "text-white" : "text-[#aaaaaa]"}`}>{s.session_id}</span>
              {s.session_id === latestId && (
                <span className="text-[9px] text-[#00FF00] border border-[#00FF00] px-1 blink">LIVE</span>
              )}
            </div>
            <div className="flex items-center gap-1 mt-1 text-[10px] text-[#888888]">
              <Cpu size={10} /> {s.model || "unknown"}
            </div>
            <div className="flex items-center justify-between mt-1 text-[10px] text-[#666666]">
              <span>turn {s.turn} · {(s.total_tokens || 0).toLocaleString()} tok</span>
              <span className="flex items-center gap-1"><Clock size={10} />{relTime(s.last_message_at)}</span>
            </div>
          </button>
        );
      })}
      {sessions.length === 0 && <div className="p-4 text-xs text-[#666666]">no sessions yet</div>}
    </div>
    <div className="px-4 py-3 border-t border-[#222222] text-[10px] text-[#555555]">
      ai-context-tracker v0.1.0 · MIT
    </div>
  </aside>
);
