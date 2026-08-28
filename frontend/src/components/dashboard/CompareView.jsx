import { useEffect, useState } from "react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const select = "w-full bg-[#0A0A0A] border border-[#333333] text-white text-xs p-2 focus:outline-none focus:border-[#00BFFF]";

const Row = ({ label, a, b, better }) => {
  const hl = (v, other) => {
    if (better === undefined || a === b) return "text-white";
    const win = better === "low" ? v < other : v > other;
    return win ? "text-[#00FF00]" : "text-white";
  };
  return (
    <div className="grid grid-cols-3 border-b border-[#1a1a1a] py-2 text-xs">
      <span className="text-[#888888]">{label}</span>
      <span className={`text-right tracking-tighter ${typeof a === "number" ? hl(a, b) : "text-white"}`}>
        {typeof a === "number" ? a.toLocaleString(undefined, { maximumFractionDigits: 4 }) : a}
      </span>
      <span className={`text-right tracking-tighter ${typeof b === "number" ? hl(b, a) : "text-white"}`}>
        {typeof b === "number" ? b.toLocaleString(undefined, { maximumFractionDigits: 4 }) : b}
      </span>
    </div>
  );
};

const Col = ({ detail }) => detail && (
  <div className="text-center border-b border-[#222222] pb-2">
    <div className="text-sm font-bold text-[#00BFFF]">{detail.model_spec.id}</div>
    <div className="text-[10px] text-[#888888]">{detail.session.session_id} · {detail.model_spec.provider}</div>
  </div>
);

export const CompareView = ({ sessions }) => {
  const [idA, setIdA] = useState(sessions[0]?.session_id || "");
  const [idB, setIdB] = useState(sessions[1]?.session_id || sessions[0]?.session_id || "");
  const [a, setA] = useState(null);
  const [b, setB] = useState(null);

  useEffect(() => {
    if (idA) axios.get(`${API}/tracker/sessions/${idA}`).then((r) => setA(r.data)).catch(() => {});
  }, [idA]);
  useEffect(() => {
    if (idB) axios.get(`${API}/tracker/sessions/${idB}`).then((r) => setB(r.data)).catch(() => {});
  }, [idB]);

  const per = (d, key) => (d.session.turn ? (key === "cost" ? d.session.cost_usd : d.session.usage.total) / d.session.turn : 0);

  return (
    <div className="p-6" data-testid="compare-view">
      <h2 className="font-heading font-bold text-sm uppercase tracking-tight mb-4">Session Compare — token & cost burn</h2>
      <div className="grid grid-cols-2 gap-4 mb-4 max-w-3xl">
        <select data-testid="compare-select-a" className={select} value={idA} onChange={(e) => setIdA(e.target.value)}>
          {sessions.map((s) => <option key={s.session_id} value={s.session_id}>{`${s.session_id} · ${s.model}`}</option>)}
        </select>
        <select data-testid="compare-select-b" className={select} value={idB} onChange={(e) => setIdB(e.target.value)}>
          {sessions.map((s) => <option key={s.session_id} value={s.session_id}>{`${s.session_id} · ${s.model}`}</option>)}
        </select>
      </div>
      {a && b && (
        <div className="border border-[#222222] bg-[#111111] p-4 max-w-3xl" data-testid="compare-table">
          <div className="grid grid-cols-3 pb-2">
            <span />
            <Col detail={a} />
            <Col detail={b} />
          </div>
          <Row label="context window" a={a.model_spec.context_window} b={b.model_spec.context_window} />
          <Row label="context used %" a={a.pct_used} b={b.pct_used} better="low" />
          <Row label="turns" a={a.session.turn} b={b.session.turn} />
          <Row label="total tokens" a={a.session.usage.total} b={b.session.usage.total} better="low" />
          <Row label="input tokens" a={a.session.usage.input} b={b.session.usage.input} />
          <Row label="output tokens" a={a.session.usage.output} b={b.session.usage.output} />
          <Row label="cached tokens" a={a.session.usage.cached} b={b.session.usage.cached} />
          <Row label="reasoning tokens" a={a.session.usage.reasoning} b={b.session.usage.reasoning} />
          <Row label="tokens / turn" a={Math.round(per(a, "tok"))} b={Math.round(per(b, "tok"))} better="low" />
          <Row label="total cost USD" a={a.session.cost_usd} b={b.session.cost_usd} better="low" />
          <Row label="cost / turn USD" a={per(a, "cost")} b={per(b, "cost")} better="low" />
          <Row label="price /1M (in · out)" a={`$${a.model_spec.price_in} · $${a.model_spec.price_out}`} b={`$${b.model_spec.price_in} · $${b.model_spec.price_out}`} />
          <p className="text-[10px] text-[#555555] mt-3">green = cheaper / lighter burn on comparable rows</p>
        </div>
      )}
    </div>
  );
};
