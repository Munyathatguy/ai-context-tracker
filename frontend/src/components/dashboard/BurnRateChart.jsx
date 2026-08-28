import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export const BurnRateChart = ({ history = [] }) => {
  const data = history.map((h) => ({ turn: h.turn, tokens: h.total, cost: h.cost }));
  return (
    <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="burn-rate-chart">
      <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">
        Burn Rate — tokens & cost over turns
      </h2>
      {data.length < 2 ? (
        <div className="text-xs text-[#666666] h-48 flex items-center" data-testid="burn-empty">
          not enough turns recorded yet — burn history appears after 2+ exchanges
        </div>
      ) : (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1c1c1c" vertical={false} />
              <XAxis dataKey="turn" stroke="#555555" tick={{ fontSize: 10, fill: "#888888" }}
                label={{ value: "turn", position: "insideBottomRight", fill: "#555555", fontSize: 10 }} />
              <YAxis yAxisId="tok" stroke="#00BFFF" tick={{ fontSize: 10, fill: "#00BFFF" }}
                tickFormatter={(v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : v)} width={44} />
              <YAxis yAxisId="usd" orientation="right" stroke="#00FF00" tick={{ fontSize: 10, fill: "#00FF00" }}
                tickFormatter={(v) => `$${v}`} width={48} />
              <Tooltip contentStyle={{ background: "#0A0A0A", border: "1px solid #333333", borderRadius: 0, fontSize: 11, fontFamily: "JetBrains Mono" }}
                labelFormatter={(t) => `turn ${t}`}
                formatter={(v, name) => (name === "cost" ? [`$${v}`, "cost"] : [v.toLocaleString(), "tokens"])} />
              <Line yAxisId="tok" type="monotone" dataKey="tokens" stroke="#00BFFF" strokeWidth={2} dot={{ r: 2, fill: "#00BFFF" }} isAnimationActive={false} />
              <Line yAxisId="usd" type="monotone" dataKey="cost" stroke="#00FF00" strokeWidth={2} dot={{ r: 2, fill: "#00FF00" }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
};
