import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";

const colorFor = (pct) => (pct < 70 ? "#00FF00" : pct < 85 ? "#FFD700" : "#FF3B30");

export const ContextGauge = ({ detail }) => {
  const pct = detail.pct_used;
  const color = colorFor(pct);
  const total = detail.session.usage.total || 0;
  const cw = detail.model_spec.context_window;
  return (
    <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="context-gauge">
      <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888]">Context Fullness</h2>
      <div className="relative h-44">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart innerRadius="70%" outerRadius="95%" data={[{ value: pct }]} startAngle={90} endAngle={-270}>
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="value" fill={color} background={{ fill: "#1c1c1c" }} isAnimationActive={false} cornerRadius={0} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-3xl font-bold tracking-tighter" style={{ color }} data-testid="context-pct">
            {pct.toFixed(1)}%
          </span>
          <span className="text-[10px] text-[#888888]">used</span>
        </div>
      </div>
      <div className="text-xs text-[#888888] text-center tracking-tighter" data-testid="context-tokens">
        {total.toLocaleString()} / {cw.toLocaleString()} tokens · <span style={{ color }}>{detail.pct_remaining.toFixed(1)}% left</span>
      </div>
    </section>
  );
};
