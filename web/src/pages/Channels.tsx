import {useEffect, useState} from 'react';
import {api, Channel} from '../api';

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const {data} = await api.get<Channel[]>('/channels');
    setChannels(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
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
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
