import {useEffect, useState} from 'react';
import {Channel, api} from '../api';
import {EmptyState, PageHeader, Stat, StatusBadge, useToast} from '../components/ui';

interface Campaign {
  id: number;
  channel_id: number;
  video_id: number | null;
  youtube_video_id: string | null;
  objective: string;
  daily_budget_usd: number;
  total_budget_usd: number;
  spend_usd: number;
  status: string;
  impressions: number;
  views: number;
  clicks: number;
  conversions: number;
}

interface Summary {
  ad_spend_usd: number;
  attributed_revenue_usd: number;
  roas: number;
}

export default function Ads() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  const load = (id: number) => {
    api.get<Campaign[]>('/ads/campaigns', {params: {channel_id: id}}).then(({data}) => setCampaigns(data));
    api.get<Summary>('/ads/summary', {params: {channel_id: id}}).then(({data}) => setSummary(data)).catch(() => setSummary(null));
  };

  useEffect(() => {
    if (selected != null) load(selected);
  }, [selected]);

  const plan = async () => {
    if (selected == null) return;
    const {data} = await api.post<Campaign[]>('/ads/plan', null, {params: {channel_id: selected}});
    push(data.length ? `Planned ${data.length} campaign(s) from budget.` : 'No new promotions — set a monthly ad budget in Settings.', data.length ? 'success' : 'info');
    load(selected);
  };
  const launch = async (id: number) => {
    await api.post(`/ads/campaigns/${id}/launch`);
    push('Campaign launched.', 'success');
    if (selected != null) load(selected);
  };
  const pause = async (id: number) => {
    await api.patch(`/ads/campaigns/${id}`, {status: 'paused'});
    if (selected != null) load(selected);
  };
  const recordSpend = async (id: number) => {
    const v = prompt('Record ad spend (USD):');
    if (!v) return;
    await api.post(`/ads/campaigns/${id}/spend`, {amount_usd: Number(v)});
    push('Ad spend recorded (counts toward ROI).', 'success');
    if (selected != null) load(selected);
  };

  return (
    <div>
      <PageHeader
        title="Paid Promotion"
        subtitle="Amplify your best videos — ad spend flows into ROI/ROAS"
        actions={
          <>
            <button onClick={plan}>Generate plan</button>
            <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 200}}>
              {channels.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </>
        }
      />

      {summary && (
        <div className="grid">
          <Stat label="Ad spend (28d)" value={`$${summary.ad_spend_usd.toLocaleString()}`} />
          <Stat label="Attributed revenue" value={`$${summary.attributed_revenue_usd.toLocaleString()}`} />
          <Stat label="ROAS" value={`${summary.roas}×`} tone={summary.roas >= 1 ? 'good' : 'bad'} />
        </div>
      )}

      <p className="muted" style={{fontSize: 12.5}}>
        Budget is set in <b>Settings → Ads</b>. The planner allocates it to your highest-retention
        videos. Without Google Ads credentials, launch campaigns manually and record spend here.
      </p>

      {campaigns.length === 0 ? (
        <EmptyState icon="📣" title="No campaigns yet" hint="Click ‘Generate plan’ to allocate your monthly budget across top videos." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>Video</th><th>Status</th><th>Daily</th><th>Total</th><th>Spent</th><th>Views</th><th></th></tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id}>
                  <td>{c.youtube_video_id ? <a href={`https://youtube.com/watch?v=${c.youtube_video_id}`} target="_blank" rel="noreferrer">#{c.video_id}</a> : `#${c.video_id}`}</td>
                  <td><StatusBadge status={c.status === 'active' ? 'running' : c.status} /></td>
                  <td>${c.daily_budget_usd}</td>
                  <td>${c.total_budget_usd}</td>
                  <td>${c.spend_usd}</td>
                  <td>{c.views.toLocaleString()}</td>
                  <td>
                    <div className="row">
                      {c.status === 'planned' && <button onClick={() => launch(c.id)}>Launch</button>}
                      {c.status === 'active' && <button className="secondary" onClick={() => pause(c.id)}>Pause</button>}
                      <button className="secondary" onClick={() => recordSpend(c.id)}>+ Spend</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
