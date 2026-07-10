import {useEffect, useState} from 'react';
import {Job, api} from '../api';
import {EmptyState, PageHeader, StatusBadge, useToast} from '../components/ui';

function Preview({videoId}: {videoId: number}) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    api.get(`/videos/${videoId}/media`).then(({data}) => setUrl(data.video_url)).catch(() => undefined);
  }, [videoId]);
  if (!url) return <span className="stat-label">Preview unavailable</span>;
  return <video src={url} controls width={160} style={{borderRadius: 8, background: '#000'}} />;
}

export default function Approvals() {
  const {push} = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);

  const load = () => api.get<Job[]>('/jobs').then(({data}) => setJobs(data));

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
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

  const statusBadge = (s: string) => {
    if (s === 'awaiting_approval') return 'warn';
    if (s === 'completed' || s === 'published') return 'ok';
    return '';
  };

  return (
    <div>
      <PageHeader title="Jobs & Approvals" subtitle="Review, approve, and monitor pipeline runs" />
      <div className="card">
        <table>
          <thead>
            <tr><th>Job</th><th>Channel</th><th>Preview</th><th>Step</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>#{j.id}</td>
                <td>{j.channel_id}</td>
                <td>{j.video_id ? <Preview videoId={j.video_id} /> : '—'}</td>
                <td>{j.current_step ?? '—'}</td>
                <td><StatusBadge status={j.status} />{j.error && <div className="stat-label">{j.error}</div>}</td>
                <td>
                  {j.status === 'awaiting_approval' && (
                    <div className="row">
                      <button onClick={() => approve(j.id)}>Approve & publish</button>
                      <button className="secondary" onClick={() => reject(j.id)}>Reject</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr><td colSpan={6} className="stat-label">No jobs yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
