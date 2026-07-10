import {useEffect, useState} from 'react';
import {CalendarEntry, Channel, api} from '../api';

export default function Calendar() {
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
    setTopic('');
    setNotes('');
    setWhen('');
    load(selected);
  };

  const remove = async (id: number) => {
    await api.delete(`/calendar/${id}`);
    if (selected != null) load(selected);
  };

  const autoPlan = async () => {
    if (selected == null) return;
    await api.post('/calendar/plan', null, {params: {channel_id: selected}});
    load(selected);
  };

  return (
    <div>
      <div className="row" style={{justifyContent: 'space-between'}}>
        <h2>Content Calendar</h2>
        <div className="row">
          <button className="secondary" onClick={autoPlan}>Auto-plan next week</button>
          <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 240}}>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        </div>
      </div>

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
        <h3>Upcoming plan</h3>
        <table>
          <thead>
            <tr><th>When</th><th>Topic</th><th>Source</th><th></th></tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td>{new Date(e.scheduled_for).toLocaleString()}</td>
                <td>{e.topic}{e.notes ? <div className="stat-label">{e.notes}</div> : null}</td>
                <td><span className={`badge ${e.locked ? 'warn' : ''}`}>{e.source === 'user' ? 'you' : 'agent'}</span></td>
                <td><button className="secondary" onClick={() => remove(e.id)}>Remove</button></td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr><td colSpan={4} className="stat-label">No planned uploads yet. The strategy agent fills this after analytics refresh.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
