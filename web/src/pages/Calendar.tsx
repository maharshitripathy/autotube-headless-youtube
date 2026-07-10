import {useEffect, useState} from 'react';
import {CalendarEntry, Channel, api} from '../api';
import {PageHeader, useToast} from '../components/ui';

export default function Calendar() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [topic, setTopic] = useState('');
  const [when, setWhen] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  const load = (channelId: number) =>
    api.get<CalendarEntry[]>('/calendar', {params: {channel_id: channelId}}).then(({data}) => setEntries(data));

  useEffect(() => {
    if (selected != null) load(selected);
  }, [selected]);

  const add = async () => {
    if (selected == null || !topic || !when) return;
    await api.post('/calendar', {
      channel_id: selected,
      topic,
      scheduled_for: new Date(when).toISOString(),
      notes: notes || null,
    });
    push('Upload added to the plan.', 'success');
    setTopic('');
    setNotes('');
    setWhen('');
    load(selected);
  };

  const remove = async (id: number) => {
    await api.delete(`/calendar/${id}`);
    push('Removed from plan.', 'info');
    if (selected != null) load(selected);
  };

  const autoPlan = async () => {
    if (selected == null) return;
    await api.post('/calendar/plan', null, {params: {channel_id: selected}});
    push('Calendar auto-planned.', 'success');
    load(selected);
  };

  const reschedule = async (id: number, dayKey: string) => {
    const entry = entries.find((e) => e.id === id);
    if (!entry) return;
    const orig = new Date(entry.scheduled_for);
    const [y, m, d] = dayKey.split('-').map(Number);
    const next = new Date(orig);
    next.setFullYear(y, m - 1, d);
    await api.patch(`/calendar/${id}`, {scheduled_for: next.toISOString()});
    push('Upload rescheduled.', 'success');
    if (selected != null) load(selected);
  };

  const dayKey = (dt: Date) => `${dt.getFullYear()}-${dt.getMonth() + 1}-${dt.getDate()}`;
  const buckets = Array.from({length: 14}).map((_, i) => {
    const dt = new Date();
    dt.setHours(0, 0, 0, 0);
    dt.setDate(dt.getDate() + i);
    return dt;
  });
  const entriesForDay = (dt: Date) => entries.filter((e) => dayKey(new Date(e.scheduled_for)) === dayKey(dt));
  const laterEntries = entries.filter((e) => {
    const dk = dayKey(new Date(e.scheduled_for));
    return !buckets.some((b) => dayKey(b) === dk);
  });

  return (
    <div>
      <PageHeader
        title="Content Calendar"
        subtitle="Plan and override upcoming uploads"
        actions={
          <>
            <button className="secondary" onClick={autoPlan}>Auto-plan next week</button>
            <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 220}}>
              {channels.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </>
        }
      />

      <div className="card">
        <h3>Add / override an upload</h3>
        <label>Topic</label>
        <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. 3 space facts that sound fake" />
        <label>Scheduled for</label>
        <input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
        <label>Additional guidance (optional)</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
        <div style={{marginTop: 12}}>
          <button onClick={add}>Add to plan</button>
        </div>
      </div>

      <div className="card">
        <div className="spread" style={{marginBottom: 6}}>
          <h3>Upcoming plan</h3>
          <span className="muted" style={{fontSize: 12}}>Drag an upload to another day to reschedule</span>
        </div>
        {entries.length === 0 && (
          <p className="stat-label">No planned uploads yet. The strategy agent fills this after analytics refresh.</p>
        )}
        <div style={{display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 8}}>
          {buckets.map((dt) => {
            const items = entriesForDay(dt);
            const key = dayKey(dt);
            return (
              <div
                key={key}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => reschedule(Number(e.dataTransfer.getData('id')), key)}
                style={{minWidth: 180, flex: '0 0 180px', background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 10, padding: 8}}
              >
                <div style={{fontSize: 12, fontWeight: 700, marginBottom: 6}}>
                  {dt.toLocaleDateString(undefined, {weekday: 'short', month: 'short', day: 'numeric'})}
                </div>
                {items.map((e) => (
                  <div
                    key={e.id}
                    draggable
                    onDragStart={(ev) => ev.dataTransfer.setData('id', String(e.id))}
                    className="card"
                    style={{padding: 8, marginBottom: 8, cursor: 'grab'}}
                  >
                    <div style={{fontSize: 12.5, fontWeight: 600}}>{e.topic}</div>
                    <div className="spread" style={{marginTop: 6}}>
                      <span className={`badge ${e.locked ? 'warn' : ''}`}>{e.source === 'user' ? 'you' : 'agent'}</span>
                      <button className="icon-btn" onClick={() => remove(e.id)}>✕</button>
                    </div>
                  </div>
                ))}
                {items.length === 0 && <div className="stat-label" style={{opacity: 0.5}}>—</div>}
              </div>
            );
          })}
        </div>
        {laterEntries.length > 0 && (
          <div style={{marginTop: 12}}>
            <div className="stat-label" style={{marginBottom: 6}}>Later</div>
            {laterEntries.map((e) => (
              <div key={e.id} className="spread" style={{padding: '6px 0', borderBottom: '1px solid var(--border)'}}>
                <span>{new Date(e.scheduled_for).toLocaleDateString()} · {e.topic}</span>
                <button className="icon-btn" onClick={() => remove(e.id)}>✕</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
