const ROWS = [
  { key: "input", label: "INPUT", color: "#00BFFF" },
  { key: "output", label: "OUTPUT", color: "#00FF00" },
  { key: "cached", label: "CACHED", color: "#888888" },
  { key: "reasoning", label: "REASONING", color: "#FFD700" },
];

export const TokenBreakdown = ({ usage }) => {
  const max = Math.max(1, ...ROWS.map((r) => usage[r.key] || 0));
  return (
    <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="token-breakdown">
      <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-4">Token Usage Breakdown</h2>
      <div className="space-y-4">
        {ROWS.map((r) => {
          const v = usage[r.key] || 0;
          return (
            <div key={r.key} data-testid={`token-row-${r.key}`}>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: r.color }}>{r.label}</span>
                <span className="text-white tracking-tighter">{v.toLocaleString()}</span>
              </div>
              <div className="h-2 bg-[#1c1c1c]">
                <div className="h-full transition-[width] duration-500" style={{ width: `${(v / max) * 100}%`, backgroundColor: r.color }} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-[#222222] flex justify-between text-sm">
        <span className="text-[#888888] text-xs uppercase">Total</span>
        <span className="font-bold tracking-tighter" data-testid="token-total">{(usage.total || 0).toLocaleString()}</span>
      </div>
    </section>
  );
};
