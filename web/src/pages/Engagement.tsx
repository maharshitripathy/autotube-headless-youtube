import {useEffect, useState} from 'react';
import {Channel, api} from '../api';
import {EmptyState, PageHeader, StatusBadge, useToast} from '../components/ui';

interface Reply {
  id: number;
  channel_id: number;
  author: string | null;
  comment_text: string | null;
  reply_text: string | null;
  action: string;
}

export default function Engagement() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [persona, setPersona] = useState('');
  const [auto, setAuto] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  const load = (id: number) => api.get<Reply[]>(`/engagement/${id}`).then(({data}) => setReplies(data));

  useEffect(() => {
    if (selected == null) return;
    load(selected);
    const ch = channels.find((c) => c.id === selected) as any;
    setPersona(ch?.engage_persona ?? '');
    setAuto(!!ch?.auto_engage);
  }, [selected]);

  const saveSettings = async () => {
    if (selected == null) return;
    await api.patch(`/channels/${selected}`, {auto_engage: auto, engage_persona: persona || null});
    push('Engagement settings saved.', 'success');
  };

  const runNow = async () => {
    if (selected == null) return;
    setRunning(true);
    try {
      const {data} = await api.post(`/engagement/${selected}/run`);
      if (data.error) push(`Engagement failed: ${data.error}`, 'error');
      else push(`Replied ${data.replied}, flagged ${data.flagged}, skipped ${data.skipped}.`, 'success');
      load(selected);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Community Engagement"
        subtitle="Auto-reply to viewer comments with a channel persona"
        actions={
          <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 220}}>
            {channels.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
          </select>
        }
      />

      <div className="card">
        <label className="row" style={{gap: 8}}>
          <input type="checkbox" style={{width: 'auto'}} checked={auto} onChange={(e) => setAuto(e.target.checked)} />
          <span>Auto-engage (replies every 4 hours)</span>
        </label>
        <label>Channel persona / reply style</label>
        <textarea rows={2} value={persona} onChange={(e) => setPersona(e.target.value)} placeholder="e.g. upbeat, witty, uses emojis, thanks viewers" />
        <div className="row" style={{marginTop: 12}}>
          <button onClick={saveSettings}>Save</button>
          <button className="secondary" onClick={runNow} disabled={running}>{running ? 'Engaging…' : 'Run engagement now'}</button>
        </div>
      </div>

      <h3 style={{margin: '18px 0 10px'}}>Recent replies</h3>
      {replies.length === 0 ? (
        <EmptyState icon="💬" title="No engagement yet" hint="Run engagement to auto-reply to recent comments." />
      ) : (
        replies.map((r) => (
          <div className="card" key={r.id}>
            <div className="spread">
              <strong>{r.author ?? 'Viewer'}</strong>
              <StatusBadge status={r.action === 'reply' ? 'completed' : r.action === 'flag' ? 'failed' : 'pending'} />
            </div>
            <p className="muted" style={{fontSize: 13, margin: '6px 0'}}>“{r.comment_text}”</p>
            {r.reply_text && <p style={{fontSize: 13.5, margin: 0}}>↳ {r.reply_text}</p>}
          </div>
        ))
      )}
    </div>
  );
}
