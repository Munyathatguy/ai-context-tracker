import { useState } from "react";
import axios from "axios";
import { CloudArrowDown } from "@phosphor-icons/react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const select = "bg-[#0A0A0A] border border-[#333333] text-white text-xs p-1.5 focus:outline-none focus:border-[#00BFFF]";

export const OrgUsagePanel = ({ defaultProvider = "openai" }) => {
  const [provider, setProvider] = useState(["openai", "anthropic", "google"].includes(defaultProvider) ? defaultProvider : "openai");
  const [days, setDays] = useState(7);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchUsage = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/tracker/org-usage`, { params: { provider, days } });
      setResult(data);
    } catch (e) {
      setResult({ error: e.response?.data?.detail || "request failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="border border-[#222222] bg-[#111111] p-4 h-full" data-testid="org-usage-panel">
      <h2 className="font-heading font-bold text-xs uppercase tracking-widest text-[#888888] mb-3">Org Usage (Admin API)</h2>
      <div className="flex items-center gap-2 mb-3">
        <select data-testid="org-provider-select" className={select} value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="openai">openai</option>
          <option value="anthropic">anthropic</option>
          <option value="google">google</option>
        </select>
        <input data-testid="org-days-input" type="number" min="1" max="31" value={days}
          onChange={(e) => setDays(parseInt(e.target.value || 1, 10))}
          className={`${select} w-16`} />
        <span className="text-[10px] text-[#888888]">days</span>
        <button data-testid="org-fetch-btn" onClick={fetchUsage} disabled={loading}
          className="ml-auto border border-[#00BFFF] text-[#00BFFF] px-2 py-1.5 text-[10px] uppercase hover:bg-[#00BFFF] hover:text-black transition-colors flex items-center gap-1">
          <CloudArrowDown size={12} /> {loading ? "…" : "fetch"}
        </button>
      </div>
      {!result && (
        <p className="text-[11px] text-[#666666]" data-testid="org-usage-hint">
          Account-wide daily token usage from the provider Admin API. Requires <span className="text-[#aaaaaa]">OPENAI_ADMIN_KEY</span> or{" "}
          <span className="text-[#aaaaaa]">ANTHROPIC_ADMIN_KEY</span> set as environment variables where the tracker runs.
        </p>
      )}
      {result && (
        <div className="text-xs space-y-1" data-testid="org-usage-result">
          {result.error && <p className="text-[#FFD700] text-[11px]">{result.error}</p>}
          {result.note && <p className="text-[#888888] text-[11px]">{result.note}</p>}
          {result.input_tokens !== undefined && (
            <>
              <div className="flex justify-between"><span className="text-[#888888]">input tokens ({result.days}d)</span><span>{result.input_tokens.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-[#888888]">output tokens ({result.days}d)</span><span>{result.output_tokens.toLocaleString()}</span></div>
            </>
          )}
        </div>
      )}
    </section>
  );
};
