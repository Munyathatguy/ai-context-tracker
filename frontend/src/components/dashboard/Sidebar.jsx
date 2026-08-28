import { useState } from "react";
import { Cpu, Clock, BoxArrowDown, Trash } from "@phosphor-icons/react";

const relTime = (iso) => {
  if (!iso) return "";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export const Sidebar = ({ sessions, selectedId, latestId, onSelect, onArchive, onDelete }) => {
  const [confirmId, setConfirmId] = useState(null);
  return (
  <aside className="w-72 shrink-0 border-r border-[#222222] bg-[#111111] flex flex-col" data-testid="sessions-sidebar">
    <div className="px-4 py-4 border-b border-[#222222]">
      <div className="text-xs uppercase tracking-widest text-[#888888] font-heading font-bold">Sessions</div>
      <div className="text-[10px] text-[#555555] mt-1">~/.ai-context-tracker/sessions</div>
    </div>
    <div className="flex-1 overflow-y-auto">
      {sessions.map((s) => {
        const active = s.session_id === selectedId;
        return (
          <div
            key={s.session_id}
            role="button"
            tabIndex={0}
            data-testid={`session-item-${s.session_id}`}
            onClick={() => onSelect(s.session_id)}
            className={`group w-full text-left px-4 py-3 border-b border-[#1a1a1a] transition-colors cursor-pointer ${
              active ? "bg-[#0A0A0A] border-l-2 border-l-[#00FF00]" : "hover:bg-[#161616]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`text-xs ${active ? "text-white" : "text-[#aaaaaa]"}`}>{s.session_id}</span>
              <span className="flex items-center gap-1.5">
                {s.session_id === latestId && (
                  <span className="text-[9px] text-[#00FF00] border border-[#00FF00] px-1 blink">LIVE</span>
                )}
                <button data-testid={`session-archive-${s.session_id}`} title="Archive session"
                  onClick={(e) => { e.stopPropagation(); setConfirmId(null); onArchive(s.session_id); }}
                  className="opacity-0 group-hover:opacity-100 text-[#888888] hover:text-[#00BFFF] transition-colors">
                  <BoxArrowDown size={13} />
                </button>
                <button data-testid={`session-delete-${s.session_id}`}
                  title={confirmId === s.session_id ? "Click again to permanently delete" : "Delete session"}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirmId === s.session_id) { setConfirmId(null); onDelete(s.session_id); }
                    else setConfirmId(s.session_id);
                  }}
                  className={`transition-colors ${confirmId === s.session_id
                    ? "opacity-100 text-[#FF3B30]" : "opacity-0 group-hover:opacity-100 text-[#888888] hover:text-[#FF3B30]"}`}>
                  <Trash size={13} weight={confirmId === s.session_id ? "fill" : "regular"} />
                </button>
              </span>
            </div>
            {confirmId === s.session_id && (
              <div className="text-[9px] text-[#FF3B30] mt-0.5" data-testid={`delete-confirm-${s.session_id}`}>click trash again to confirm delete</div>
            )}
            <div className="flex items-center gap-1 mt-1 text-[10px] text-[#888888]">
              <Cpu size={10} /> {s.model || "unknown"}
            </div>
            <div className="flex items-center justify-between mt-1 text-[10px] text-[#666666]">
              <span>turn {s.turn} · {(s.total_tokens || 0).toLocaleString()} tok</span>
              <span className="flex items-center gap-1"><Clock size={10} />{relTime(s.last_message_at)}</span>
            </div>
          </div>
        );
      })}
      {sessions.length === 0 && <div className="p-4 text-xs text-[#666666]">no sessions yet</div>}
    </div>
    <div className="px-4 py-3 border-t border-[#222222] text-[10px] text-[#555555]">
      ai-context-tracker v0.1.0 · MIT
    </div>
  </aside>
  );
};
