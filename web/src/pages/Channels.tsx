import {useEffect, useState} from 'react';
import {api, Channel} from '../api';
import {EmptyState, PageHeader, SkeletonCards, useToast} from '../components/ui';
import {OnboardingWizard} from '../components/OnboardingWizard';

interface Voice {
  voice_id: string;
  name: string;
}

function ChannelSettings({channel, voices, onSaved}: {channel: Channel; voices: Voice[]; onSaved: () => void}) {
  const {push} = useToast();
  const [niche, setNiche] = useState(channel.niche ?? '');
  const [uploads, setUploads] = useState(channel.uploads_per_day);
  const [voiceId, setVoiceId] = useState('');
  const [cap, setCap] = useState(0);
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [musicUrl, setMusicUrl] = useState('');
  const [heroProvider, setHeroProvider] = useState('');

  const togglePlatform = (p: string) => {
    setPlatforms((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]));
  };

  const save = async () => {
    await api.patch(`/channels/${channel.id}`, {
      niche: niche || null,
      uploads_per_day: uploads,
      voice_id: voiceId || null,
      daily_cost_cap_usd: cap,
      distribute_platforms: platforms,
      music_url: musicUrl || null,
      hero_video_provider: heroProvider || null,
    });
    push('Channel settings saved.', 'success');
    onSaved();
  };

  return (
    <div style={{marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 12}}>
      <label>Niche</label>
      <input value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="e.g. space facts" />
      <label>Uploads per day</label>
      <input type="number" min={1} max={12} value={uploads} onChange={(e) => setUploads(Number(e.target.value))} />
      <label>Narration voice</label>
      <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
        <option value="">Default</option>
        {voices.map((v) => (
          <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
        ))}
      </select>
      <label>Daily cost cap (USD, 0 = global default)</label>
      <input type="number" min={0} step={0.5} value={cap} onChange={(e) => setCap(Number(e.target.value))} />
      <label>Cross-post to</label>
      <div className="row">
        {['tiktok', 'reels'].map((p) => (
          <span
            key={p}
            className={`badge ${platforms.includes(p) ? 'ok' : ''}`}
            style={{cursor: 'pointer'}}
            onClick={() => togglePlatform(p)}
          >
            {p}
          </span>
        ))}
      </div>
      <label>Background music URL (royalty-free, optional)</label>
      <input value={musicUrl} onChange={(e) => setMusicUrl(e.target.value)} placeholder="https://... .mp3" />
      <label>AI hero-clip provider</label>
      <select value={heroProvider} onChange={(e) => setHeroProvider(e.target.value)}>
        <option value="">Default</option>
        <option value="veo">Google Veo 3</option>
        <option value="runway">Runway Gen-4</option>
        <option value="luma">Luma Dream Machine</option>
        <option value="kling">Kling</option>
        <option value="none">None (stock/AI images only)</option>
      </select>
      <div style={{marginTop: 12}}>
        <button onClick={save}>Save settings</button>
      </div>
    </div>
  );
}

export default function Channels() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [presetId, setPresetId] = useState('');
  const [selected, setSelected] = useState<number[]>([]);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState<'connect' | 'configure'>('connect');

  const toggleSelect = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const load = async () => {
    setLoading(true);
    const {data} = await api.get<Channel[]>('/channels');
    setChannels(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
    api.get<Voice[]>('/channels/voices').then(({data}) => setVoices(data)).catch(() => undefined);
    api.get('/bulk/presets').then(({data}) => setPresets(data)).catch(() => undefined);
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected')) {
      push('Channel connected successfully.', 'success');
      setWizardStep('configure');
      setWizardOpen(true);
    }
    if (params.get('error')) push(`Connection failed: ${params.get('error')}`, 'error');
  }, []);

  const applyPreset = async () => {
    if (!presetId || selected.length === 0) return;
    await api.post('/bulk/presets/apply', {channel_ids: selected, preset_id: presetId});
    push('Preset applied and calendar seeded.', 'success');
    setSelected([]);
    load();
  };
  const bulkRun = async () => {
    if (selected.length === 0) return;
    await api.post('/bulk/channels/run', {channel_ids: selected});
    push(`Started pipelines for ${selected.length} channel(s).`, 'success');
  };
  const bulkAutonomy = async (on: boolean) => {
    if (selected.length === 0) return;
    await api.post('/bulk/channels/autonomy', {channel_ids: selected, autonomous: on});
    push(`Autonomy turned ${on ? 'on' : 'off'} for ${selected.length} channel(s).`, 'success');
    load();
  };

  const onboard = async () => {
    const {data} = await api.get('/auth/youtube/start');
    window.location.href = data.authorization_url;
  };

  const runNow = async (channelId: number) => {
    await api.post('/jobs', {channel_id: channelId});
    push('Pipeline started. Check Approvals if approval is required.', 'success');
  };

  const toggle = async (c: Channel, field: 'autonomous' | 'require_approval') => {
    await api.patch(`/channels/${c.id}`, {[field]: !c[field]});
    load();
  };

  return (
    <div>
      <PageHeader
        title="Channels"
        subtitle="Onboard, configure, and run your channel empire"
        actions={
          <>
            <button className="secondary" onClick={() => { setWizardStep(channels.length ? 'configure' : 'connect'); setWizardOpen(true); }}>Setup wizard</button>
            <button onClick={onboard}>+ Connect / initiate channel</button>
          </>
        }
      />

      <OnboardingWizard
        open={wizardOpen}
        startStep={wizardStep}
        channels={channels}
        onClose={() => setWizardOpen(false)}
        onDone={load}
      />

      {channels.length > 0 && (
        <div className="card">
          <div className="row" style={{flexWrap: 'wrap', gap: 10}}>
            <strong>{selected.length} selected</strong>
            <select value={presetId} onChange={(e) => setPresetId(e.target.value)} style={{width: 200}}>
              <option value="">Choose preset…</option>
              {presets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <button className="secondary" onClick={applyPreset}>Apply preset</button>
            <button onClick={bulkRun}>Run selected</button>
            <button className="secondary" onClick={() => bulkAutonomy(true)}>Autonomy on</button>
            <button className="secondary" onClick={() => bulkAutonomy(false)}>Autonomy off</button>
          </div>
        </div>
      )}

      {loading ? (
        <SkeletonCards count={4} />
      ) : channels.length === 0 ? (
        <EmptyState
          icon="📺"
          title="No channels connected yet"
          hint="Connect an existing YouTube channel via OAuth to start automating."
          action={<button onClick={() => { setWizardStep('connect'); setWizardOpen(true); }}>Start setup wizard</button>}
        />
      ) : (
        <div className="grid">
          {channels.map((c) => (
            <div className="card" key={c.id}>
              <div className="row">
                <input type="checkbox" style={{width: 'auto'}} checked={selected.includes(c.id)} onChange={() => toggleSelect(c.id)} />
                {c.thumbnail_url && (
                  <img src={c.thumbnail_url} width={40} height={40} style={{borderRadius: 8}} />
                )}
                <div>
                  <strong>{c.title}</strong>
                  <div className="stat-label">{c.handle ?? c.youtube_channel_id}</div>
                </div>
              </div>
              <div style={{marginTop: 12}} className="row">
                <span className={`badge ${c.autonomous ? 'ok' : ''}`} onClick={() => toggle(c, 'autonomous')} style={{cursor: 'pointer'}}>
                  {c.autonomous ? 'Autonomous' : 'Manual'}
                </span>
                <span className={`badge ${c.require_approval ? 'warn' : 'ok'}`} onClick={() => toggle(c, 'require_approval')} style={{cursor: 'pointer'}}>
                  {c.require_approval ? 'Approval required' : 'Auto-publish'}
                </span>
              </div>
              <div style={{marginTop: 14}} className="row">
                <button onClick={() => runNow(c.id)}>Run now</button>
                <button className="secondary" onClick={() => setExpanded(expanded === c.id ? null : c.id)}>
                  {expanded === c.id ? 'Close' : 'Settings'}
                </button>
              </div>
              {expanded === c.id && (
                <ChannelSettings channel={c} voices={voices} onSaved={() => { setExpanded(null); load(); }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
