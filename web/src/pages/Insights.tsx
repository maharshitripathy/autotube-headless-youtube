import {useEffect, useState} from 'react';
import {AnalyticsSummary, Channel, api} from '../api';
import {EmptyState, PageHeader, Stat, useToast} from '../components/ui';

interface DailyPoint {
  day: string;
  views: number;
  watch_time_minutes: number;
  subscribers_gained: number;
}

interface Revenue {
  estimated_revenue_usd: number;
  production_spend_usd: number;
  net_profit_usd: number;
  avg_rpm_usd: number;
  roi_pct: number;
}

function ViewsChart({data}: {data: DailyPoint[]}) {
  if (data.length === 0) return <p className="stat-label">No daily data yet. Click Refresh to pull analytics.</p>;
  const max = Math.max(1, ...data.map((d) => d.views));
  const w = 640;
  const h = 160;
  const bw = w / data.length;
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{maxWidth: w}}>
      {data.map((d, i) => {
        const bh = (d.views / max) * (h - 20);
        return (
          <rect
            key={d.day}
            x={i * bw + 2}
            y={h - bh}
            width={Math.max(1, bw - 4)}
            height={bh}
            rx={2}
            fill="#4d9bff"
          >
            <title>{`${d.day}: ${d.views} views`}</title>
          </rect>
        );
      })}
    </svg>
  );
}

export default function Insights() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [daily, setDaily] = useState<DailyPoint[]>([]);
  const [revenue, setRevenue] = useState<Revenue | null>(null);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (selected == null) return;
    api.get<AnalyticsSummary>(`/analytics/${selected}/summary`).then(({data}) => setSummary(data));
    api.get<DailyPoint[]>(`/analytics/${selected}/daily`).then(({data}) => setDaily(data)).catch(() => setDaily([]));
    api.get<Revenue>(`/analytics/${selected}/revenue`).then(({data}) => setRevenue(data)).catch(() => setRevenue(null));
  }, [selected]);

  const refresh = async () => {
    if (selected == null) return;
    await api.post(`/analytics/${selected}/refresh`);
    push('Analytics refresh queued.', 'success');
  };

  return (
    <div>
      <PageHeader
        title="Insights"
        subtitle="Performance and revenue per channel"
        actions={
          <>
            <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 220}}>
              {channels.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
            <button className="secondary" onClick={refresh}>Refresh</button>
          </>
        }
      />

      {summary ? (
        <div className="grid">
          <Stat label="Views (28d)" value={summary.total_views.toLocaleString()} />
          <Stat label="Watch time (min)" value={Math.round(summary.total_watch_time_minutes).toLocaleString()} />
          <Stat label="Subscribers gained" value={summary.subscribers_gained.toLocaleString()} />
          <Stat label="Avg CTR" value={`${(summary.avg_ctr * 100).toFixed(1)}%`} />
          <Stat label="Videos published" value={summary.videos_published} />
        </div>
      ) : (
        <EmptyState icon="📈" title="No analytics yet" hint="Select a channel and hit Refresh to pull the latest metrics." />
      )}

      <div className="card">
        <h3>Daily views (28d)</h3>
        <ViewsChart data={daily} />
      </div>

      {revenue && (
        <>
          <h3 style={{margin: '18px 0 10px'}}>Revenue &amp; ROI (28d)</h3>
          <div className="grid">
            <Stat label="Est. ad revenue" value={`$${revenue.estimated_revenue_usd.toLocaleString()}`} />
            <Stat label="Production spend" value={`$${revenue.production_spend_usd.toLocaleString()}`} />
            <Stat label="Net profit" value={`$${revenue.net_profit_usd.toLocaleString()}`} tone={revenue.net_profit_usd >= 0 ? 'good' : 'bad'} />
            <Stat label="Avg RPM" value={`$${revenue.avg_rpm_usd}`} />
            <Stat label="ROI" value={`${revenue.roi_pct}%`} tone={revenue.roi_pct >= 0 ? 'good' : 'bad'} />
          </div>
        </>
      )}
    </div>
  );
}
