import {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {api} from '../api';
import {EmptyState, PageHeader, SkeletonCards, Stat} from '../components/ui';

interface Overview {
  totals: {
    channels: number;
    views: number;
    revenue_usd: number;
    spend_usd: number;
    profit_usd: number;
    videos_published: number;
  };
  leaderboard: {
    channel_id: number;
    title: string;
    thumbnail_url: string | null;
    views: number;
    revenue_usd: number;
    profit_usd: number;
    videos_published: number;
    autonomous: boolean;
  }[];
  activity: {
    id: number;
    channel_id: number;
    status: string;
    step: string | null;
    trigger: string;
    created_at: string | null;
  }[];
}

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export default function Dashboard() {
  const nav = useNavigate();
  const [data, setData] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Overview>('/system/overview')
      .then(({data}) => setData(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Empire Overview" subtitle="Everything across your channels, at a glance" />

      {loading ? (
        <SkeletonCards count={6} />
      ) : !data || data.totals.channels === 0 ? (
        <EmptyState
          icon="🚀"
          title="Your empire is empty"
          hint="Connect a channel to start seeing performance here."
          action={<button onClick={() => nav('/channels')}>Go to Channels</button>}
        />
      ) : (
        <>
          <div className="grid">
            <Stat label="Channels" value={data.totals.channels} />
            <Stat label="Views (28d)" value={data.totals.views.toLocaleString()} />
            <Stat label="Revenue (28d)" value={`$${data.totals.revenue_usd.toLocaleString()}`} />
            <Stat label="Spend (28d)" value={`$${data.totals.spend_usd.toLocaleString()}`} />
            <Stat label="Net profit (28d)" value={`$${data.totals.profit_usd.toLocaleString()}`} tone={data.totals.profit_usd >= 0 ? 'good' : 'bad'} />
            <Stat label="Videos published" value={data.totals.videos_published} />
          </div>

          <div style={{display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, marginTop: 8}}>
            <div className="card">
              <div className="spread" style={{marginBottom: 8}}>
                <h3>🏆 Profit leaderboard</h3>
                <span className="muted" style={{fontSize: 12}}>28-day</span>
              </div>
              <table>
                <thead>
                  <tr><th>#</th><th>Channel</th><th>Views</th><th>Revenue</th><th>Profit</th></tr>
                </thead>
                <tbody>
                  {data.leaderboard.map((c, i) => (
                    <tr key={c.channel_id} style={{cursor: 'pointer'}} onClick={() => nav('/insights')}>
                      <td>{i + 1}</td>
                      <td>
                        <div className="row" style={{gap: 8}}>
                          {c.thumbnail_url && <img src={c.thumbnail_url} width={26} height={26} style={{borderRadius: 6}} />}
                          <span>{c.title}</span>
                          {c.autonomous && <span className="badge ok">auto</span>}
                        </div>
                      </td>
                      <td>{c.views.toLocaleString()}</td>
                      <td>${c.revenue_usd.toLocaleString()}</td>
                      <td style={{color: c.profit_usd >= 0 ? 'var(--good)' : 'var(--bad)'}}>${c.profit_usd.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3 style={{marginBottom: 10}}>⚡ Recent activity</h3>
              {data.activity.length === 0 && <p className="muted">No pipeline runs yet.</p>}
              {data.activity.map((a) => (
                <div key={a.id} className="spread" style={{padding: '8px 0', borderBottom: '1px solid var(--border)'}}>
                  <div>
                    <div style={{fontSize: 13.5}}>Job #{a.id} · ch {a.channel_id}</div>
                    <div className="stat-label">{a.step ?? a.status} · {a.trigger}</div>
                  </div>
                  <div style={{textAlign: 'right'}}>
                    <span className={`badge ${a.status === 'completed' ? 'ok' : a.status === 'failed' ? 'bad' : a.status === 'awaiting_approval' ? 'warn' : 'info'}`}>{a.status.replace(/_/g, ' ')}</span>
                    <div className="stat-label">{timeAgo(a.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
