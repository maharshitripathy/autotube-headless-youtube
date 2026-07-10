import {useEffect, useState} from 'react';
import {api} from '../api';
import {PageHeader, useToast} from '../components/ui';

interface Config {
  providers: Record<string, boolean>;
  video_provider: string;
  whisper_model: string;
  cost_caps: {per_video_usd: number; per_channel_daily_usd: number; global_daily_usd: number};
  ads: {monthly_ad_budget_usd: number; ad_auto_promote: boolean; ad_target_roas: number};
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI', elevenlabs: 'ElevenLabs', pexels: 'Pexels', youtube_oauth: 'YouTube OAuth',
  veo: 'Google Veo', runway: 'Runway', luma: 'Luma', kling: 'Kling',
};

export default function Settings() {
  const {push} = useToast();
  const [cfg, setCfg] = useState<Config | null>(null);
  const [caps, setCaps] = useState({per_video: 0, per_channel: 0, global: 0});
  const [ads, setAds] = useState({budget: 0, auto: false, roas: 2});
  const [theme, setTheme] = useState(localStorage.getItem('autotube_theme') ?? 'dark');

  useEffect(() => {
    api.get<Config>('/system/config').then(({data}) => {
      setCfg(data);
      setCaps({
        per_video: data.cost_caps.per_video_usd,
        per_channel: data.cost_caps.per_channel_daily_usd,
        global: data.cost_caps.global_daily_usd,
      });
      setAds({budget: data.ads.monthly_ad_budget_usd, auto: data.ads.ad_auto_promote, roas: data.ads.ad_target_roas});
    });
  }, []);

  const applyTheme = (t: string) => {
    setTheme(t);
    localStorage.setItem('autotube_theme', t);
    document.documentElement.setAttribute('data-theme', t);
  };

  const saveCaps = async () => {
    await api.put('/system/config', {
      cost_cap_per_video_usd: caps.per_video,
      cost_cap_per_channel_daily_usd: caps.per_channel,
      cost_cap_global_daily_usd: caps.global,
    });
    push('Cost caps saved.', 'success');
  };

  const saveAds = async () => {
    await api.put('/system/config', {
      monthly_ad_budget_usd: ads.budget,
      ad_auto_promote: ads.auto,
      ad_target_roas: ads.roas,
    });
    push('Ad settings saved.', 'success');
  };

  return (
    <div>
      <PageHeader title="Settings" subtitle="Providers, cost guardrails, and appearance" />

      <div className="card">
        <h3>Provider connections</h3>
        <p className="muted" style={{fontSize: 12.5, marginTop: 0}}>Keys are configured in your <code>.env</code>. Green = connected.</p>
        <div className="row wrap" style={{gap: 8}}>
          {cfg && Object.entries(cfg.providers).map(([k, v]) => (
            <span key={k} className={`badge ${v ? 'ok' : 'bad'}`}>{PROVIDER_LABELS[k] ?? k}: {v ? 'connected' : 'not set'}</span>
          ))}
        </div>
        {cfg && (
          <p className="muted" style={{fontSize: 12.5, marginTop: 12}}>
            Active AI-video provider: <b>{cfg.video_provider}</b> · Captions model: <b>{cfg.whisper_model}</b>
          </p>
        )}
      </div>

      <div className="card">
        <h3>Cost guardrails (USD)</h3>
        <p className="muted" style={{fontSize: 12.5, marginTop: 0}}>Hard caps enforced before any paid API call. 0 disables a cap.</p>
        <div className="grid">
          <div>
            <label>Per video</label>
            <input type="number" min={0} step={0.25} value={caps.per_video} onChange={(e) => setCaps({...caps, per_video: Number(e.target.value)})} />
          </div>
          <div>
            <label>Per channel / day</label>
            <input type="number" min={0} step={1} value={caps.per_channel} onChange={(e) => setCaps({...caps, per_channel: Number(e.target.value)})} />
          </div>
          <div>
            <label>Global / day</label>
            <input type="number" min={0} step={1} value={caps.global} onChange={(e) => setCaps({...caps, global: Number(e.target.value)})} />
          </div>
        </div>
        <div style={{marginTop: 12}}><button onClick={saveCaps}>Save cost caps</button></div>
      </div>

      <div className="card">
        <h3>Paid promotion (ads)</h3>
        <p className="muted" style={{fontSize: 12.5, marginTop: 0}}>The planner allocates this monthly budget across your best videos. Ad spend counts toward ROI.</p>
        <div className="grid">
          <div>
            <label>Monthly ad budget (USD)</label>
            <input type="number" min={0} step={5} value={ads.budget} onChange={(e) => setAds({...ads, budget: Number(e.target.value)})} />
          </div>
          <div>
            <label>Target ROAS</label>
            <input type="number" min={0} step={0.1} value={ads.roas} onChange={(e) => setAds({...ads, roas: Number(e.target.value)})} />
          </div>
        </div>
        <label className="row" style={{gap: 8, marginTop: 12}}>
          <input type="checkbox" style={{width: 'auto'}} checked={ads.auto} onChange={(e) => setAds({...ads, auto: e.target.checked})} />
          <span>Auto-plan promotions daily within budget</span>
        </label>
        <div style={{marginTop: 12}}><button onClick={saveAds}>Save ad settings</button></div>
      </div>

      <div className="card">
        <h3>Appearance</h3>
        <div className="row">
          <button className={theme === 'dark' ? '' : 'secondary'} onClick={() => applyTheme('dark')}>🌙 Dark</button>
          <button className={theme === 'light' ? '' : 'secondary'} onClick={() => applyTheme('light')}>☀️ Light</button>
        </div>
      </div>
    </div>
  );
}
