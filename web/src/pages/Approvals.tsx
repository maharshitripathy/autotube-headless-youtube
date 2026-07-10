import {useEffect, useState} from 'react';
import {Job, api} from '../api';
import {EmptyState, PageHeader, StatusBadge, useToast} from '../components/ui';

const STEPS = ['research', 'script', 'voiceover', 'visuals', 'captions', 'render', 'seo', 'publish'];

function Preview({videoId}: {videoId: number}) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    api.get(`/videos/${videoId}/media`).then(({data}) => setUrl(data.video_url)).catch(() => undefined);
  }, [videoId]);
  if (!url) return <div className="thumb-sm" style={{display: 'grid', placeItems: 'center', color: 'var(--muted)'}}>🎬</div>;
  return <video src={url} controls className="thumb-sm" style={{width: 80}} />;
}

function Stepper({job}: {job: Job}) {
  const terminal = ['completed', 'published'].includes(job.status);
  const failed = ['failed', 'rejected'].includes(job.status);
  const currentIdx = job.current_step ? STEPS.indexOf(job.current_step) : -1;
  const doneCount = terminal ? STEPS.length : Math.max(0, currentIdx);
  const pct = Math.round((doneCount / STEPS.length) * 100);

  return (
    <div>
      <div className="stepper">
        {STEPS.map((s, i) => {
          const done = terminal || i < currentIdx;
          const active = !terminal && !failed && i === currentIdx;
          return (
            <div key={s} className={`step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
              <span className="dot" />
              <span>{s}</span>
              {i < STEPS.length - 1 && <span className="arr">›</span>}
            </div>
          );
        })}
      </div>
      <div className="progress" style={{marginTop: 8}}>
        <span style={{width: `${failed ? 100 : pct}%`, background: failed ? 'var(--bad)' : undefined}} />
      </div>
    </div>
  );
}

export default function Approvals() {
  const {push} = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filter, setFilter] = useState('all');

  const load = () => api.get<Job[]>('/jobs').then(({data}) => setJobs(data));

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  const approve = async (id: number) => {
    await api.post(`/jobs/${id}/approve`);
    push('Approved — publishing now.', 'success');
    load();
  };
  const reject = async (id: number) => {
    await api.post(`/jobs/${id}/reject`);
    push('Job rejected.', 'info');
    load();
  };

  const filtered = jobs.filter((j) => {
    if (filter === 'all') return true;
    if (filter === 'active') return ['pending', 'running', 'awaiting_approval'].includes(j.status);
    return j.status === filter;
  });

  const awaiting = jobs.filter((j) => j.status === 'awaiting_approval');

  return (
    <div>
      <PageHeader
        title="Jobs & Approvals"
        subtitle="Live pipeline progress and the approval queue"
        actions={
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{width: 160}}>
            <option value="all">All jobs</option>
            <option value="active">Active</option>
            <option value="awaiting_approval">Awaiting approval</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        }
      />

      {awaiting.length > 0 && (
        <div className="card" style={{borderColor: 'var(--warn)'}}>
          <strong>⏳ {awaiting.length} video{awaiting.length === 1 ? '' : 's'} awaiting your approval</strong>
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState icon="🛠️" title="No jobs to show" hint="Trigger a run from Channels or wait for the scheduler." />
      ) : (
        filtered.map((j) => (
          <div className="card" key={j.id}>
            <div className="row" style={{gap: 14, alignItems: 'flex-start'}}>
              {j.video_id && <Preview videoId={j.video_id} />}
              <div style={{flex: 1, minWidth: 0}}>
                <div className="spread">
                  <div>
                    <strong>Job #{j.id}</strong>{' '}
                    <span className="muted" style={{fontSize: 12}}>· channel {j.channel_id} · {j.trigger}</span>
                  </div>
                  <StatusBadge status={j.status} />
                </div>
                <div style={{marginTop: 10}}>
                  <Stepper job={j} />
                </div>
                {j.error && <div className="stat-label" style={{color: 'var(--bad)', marginTop: 6}}>{j.error}</div>}
                {j.status === 'awaiting_approval' && (
                  <div className="row" style={{marginTop: 12}}>
                    <button onClick={() => approve(j.id)}>Approve & publish</button>
                    <button className="secondary" onClick={() => reject(j.id)}>Reject</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
