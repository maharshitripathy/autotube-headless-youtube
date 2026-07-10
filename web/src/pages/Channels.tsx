import {useEffect, useState} from 'react';
import {api, Channel} from '../api';

interface Voice {
  voice_id: string;
  name: string;
}

function ChannelSettings({channel, voices, onSaved}: {channel: Channel; voices: Voice[]; onSaved: () => void}) {
  const [niche, setNiche] = useState(channel.niche ?? '');
  const [uploads, setUploads] = useState(channel.uploads_per_day);
  const [voiceId, setVoiceId] = useState('');
  const [cap, setCap] = useState(0);
  const [platforms, setPlatforms] = useState<string[]>([]);

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
    });
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
      <div style={{marginTop: 12}}>
        <button onClick={save}>Save settings</button>
      </div>
    </div>
  );
}

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [banner, setBanner] = useState<string>('');

  const load = async () => {
    setLoading(true);
    const {data} = await api.get<Channel[]>('/channels');
    setChannels(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
    api.get<Voice[]>('/channels/voices').then(({data}) => setVoices(data)).catch(() => undefined);
    const params = new URLSearchParams(window.location.search);
    if (params.get('connected')) setBanner('Channel connected successfully.');
    if (params.get('error')) setBanner(`Connection failed: ${params.get('error')}`);
  }, []);

  const onboard = async () => {
    // Kick off the guided OAuth wizard (P1).
    const {data} = await api.get('/auth/youtube/start');
    window.location.href = data.authorization_url;
  };

  const runNow = async (channelId: number) => {
    await api.post('/jobs', {channel_id: channelId});
    alert('Pipeline started. Check Approvals if approval is required.');
  };

  const toggle = async (c: Channel, field: 'autonomous' | 'require_approval') => {
    await api.patch(`/channels/${c.id}`, {[field]: !c[field]});
    load();
  };

  return (
    <div>
      <div className="row" style={{justifyContent: 'space-between'}}>
        <h2>Channels</h2>
        <button onClick={onboard}>+ Connect / initiate channel</button>
      </div>

      {banner && <div className="card"><span className="badge ok">{banner}</span></div>}

      {loading ? (
        <p>Loading…</p>
      ) : channels.length === 0 ? (
        <div className="card">
          <p>No channels connected yet.</p>
          <p className="stat-label">
            Click “Connect / initiate channel” to authorize an existing YouTube channel via OAuth.
          </p>
        </div>
      ) : (
        <div className="grid">
          {channels.map((c) => (
            <div className="card" key={c.id}>
              <div className="row">
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
