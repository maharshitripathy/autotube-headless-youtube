import {useEffect, useState} from 'react';
import {AnalyticsSummary, Channel, api} from '../api';

export default function Insights() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (selected == null) return;
    api.get<AnalyticsSummary>(`/analytics/${selected}/summary`).then(({data}) => setSummary(data));
  }, [selected]);

  const refresh = async () => {
    if (selected == null) return;
    await api.post(`/analytics/${selected}/refresh`);
    alert('Analytics refresh queued.');
  };

  return (
    <div>
      <div className="row" style={{justifyContent: 'space-between'}}>
        <h2>Insights</h2>
        <div className="row">
          <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 240}}>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
          <button className="secondary" onClick={refresh}>Refresh</button>
        </div>
      </div>

      {summary ? (
        <div className="grid">
          <div className="card"><div className="stat">{summary.total_views.toLocaleString()}</div><div className="stat-label">Views (28d)</div></div>
          <div className="card"><div className="stat">{Math.round(summary.total_watch_time_minutes).toLocaleString()}</div><div className="stat-label">Watch time (min)</div></div>
          <div className="card"><div className="stat">{summary.subscribers_gained.toLocaleString()}</div><div className="stat-label">Subscribers gained</div></div>
          <div className="card"><div className="stat">{(summary.avg_ctr * 100).toFixed(1)}%</div><div className="stat-label">Avg CTR</div></div>
          <div className="card"><div className="stat">{summary.videos_published}</div><div className="stat-label">Videos published</div></div>
        </div>
      ) : (
        <p>Select a channel to view analytics.</p>
      )}
    </div>
  );
}
