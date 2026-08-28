import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { GearSix } from "@phosphor-icons/react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Button } from "../ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FEATURE_LABELS = {
  token_tracking: "Token tracking",
  time_awareness: "Time awareness",
  context_health: "Context health",
  session_continuity: "Session continuity",
  model_awareness: "Model awareness",
  task_tracking: "Task tracking",
  cost_tracking: "Cost tracking",
  turn_counter: "Turn counter",
};

const field = "bg-[#0A0A0A] border-[#333333] rounded-none text-white text-xs h-8 focus-visible:ring-[#00BFFF]";

export const SettingsDialog = () => {
  const [open, setOpen] = useState(false);
  const [cfg, setCfg] = useState(null);
  const [thresholds, setThresholds] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    axios.get(`${API}/tracker/config`).then(({ data }) => {
      setCfg(data);
      setThresholds(data.alert_thresholds.join(", "));
    }).catch(() => toast.error("Failed to load config"));
  }, [open]);

  const save = async () => {
    const parsed = thresholds.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n));
    if (parsed.length === 0) return toast.error("Enter at least one threshold (1-99)");
    setSaving(true);
    try {
      const { data } = await axios.put(`${API}/tracker/config`, {
        alert_thresholds: parsed,
        red_alert_threshold: cfg.red_alert_threshold,
        danger_threshold: cfg.danger_threshold,
        auto_handoff: cfg.auto_handoff,
        timezone: cfg.timezone,
        features: cfg.features,
      });
      setCfg(data);
      setThresholds(data.alert_thresholds.join(", "));
      toast.success("Config saved to " + data.config_path);
      setOpen(false);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button data-testid="settings-open-btn" title="Threshold & config editor"
          className="border border-[#333333] p-1.5 text-[#888888] hover:text-white hover:border-[#00BFFF] transition-colors">
          <GearSix size={16} weight="duotone" />
        </button>
      </DialogTrigger>
      <DialogContent className="bg-[#111111] border border-[#333333] rounded-none text-white font-mono max-w-md" data-testid="settings-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading uppercase tracking-tight text-sm">Tracker Configuration</DialogTitle>
        </DialogHeader>
        {!cfg ? <div className="text-xs text-[#888888]">loading…</div> : (
          <div className="space-y-4">
            <div>
              <Label className="text-[10px] uppercase text-[#888888]">Alert thresholds (% remaining, comma-separated)</Label>
              <Input data-testid="thresholds-input" className={field} value={thresholds}
                onChange={(e) => setThresholds(e.target.value)} placeholder="30, 20, 10" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-[10px] uppercase text-[#888888]">Red alert ≤ %</Label>
                <Input data-testid="red-threshold-input" type="number" className={field} value={cfg.red_alert_threshold}
                  onChange={(e) => setCfg({ ...cfg, red_alert_threshold: parseInt(e.target.value || 0, 10) })} />
              </div>
              <div>
                <Label className="text-[10px] uppercase text-[#888888]">Danger zone ≤ %</Label>
                <Input data-testid="danger-threshold-input" type="number" className={field} value={cfg.danger_threshold}
                  onChange={(e) => setCfg({ ...cfg, danger_threshold: parseInt(e.target.value || 0, 10) })} />
              </div>
            </div>
            <div>
              <Label className="text-[10px] uppercase text-[#888888]">Timezone (IANA)</Label>
              <Input data-testid="timezone-input" className={field} value={cfg.timezone}
                onChange={(e) => setCfg({ ...cfg, timezone: e.target.value })} placeholder="America/New_York" />
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-xs">Auto-handoff at danger threshold</Label>
              <Switch data-testid="auto-handoff-switch" checked={cfg.auto_handoff}
                onCheckedChange={(v) => setCfg({ ...cfg, auto_handoff: v })} />
            </div>
            <div>
              <Label className="text-[10px] uppercase text-[#888888]">Features</Label>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-2">
                {Object.entries(FEATURE_LABELS).map(([k, label]) => (
                  <div key={k} className="flex items-center justify-between">
                    <span className="text-[11px] text-[#cccccc]">{label}</span>
                    <Switch data-testid={`feature-${k}-switch`} checked={!!cfg.features?.[k]}
                      onCheckedChange={(v) => setCfg({ ...cfg, features: { ...cfg.features, [k]: v } })} />
                  </div>
                ))}
              </div>
            </div>
            <Button data-testid="settings-save-btn" onClick={save} disabled={saving}
              className="w-full rounded-none bg-[#00FF00] text-black hover:bg-[#00cc00] font-bold text-xs uppercase">
              {saving ? "Saving…" : "Save config.yaml"}
            </Button>
            <p className="text-[10px] text-[#555555]">Written to {cfg.config_path}. The MCP server picks it up on next start; alerts use these values immediately for new sessions.</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
