import {useEffect, useState} from 'react';
import {Channel, api} from '../api';
import {EmptyState, PageHeader, useToast} from '../components/ui';

interface Result {
  index: number;
  title: string;
  views: number;
}

interface Experiment {
  id: number;
  video_id: number;
  channel_id: number;
  variants: string[];
  current_index: number;
  results: Result[] | null;
  settled: boolean;
  winner_index: number | null;
}

export default function Experiments() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [experiments, setExperiments] = useState<Experiment[]>([]);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  const load = (channelId: number) =>
    api.get<Experiment[]>('/experiments', {params: {channel_id: channelId}}).then(({data}) => setExperiments(data));

  useEffect(() => {
    if (selected != null) load(selected);
  }, [selected]);

  const promote = async (exp: Experiment, index: number) => {
    await api.post(`/experiments/${exp.id}/promote/${index}`);
    push(`Promoted variant ${index + 1} as the winner.`, 'success');
    if (selected != null) load(selected);
  };

  const viewsFor = (exp: Experiment, index: number) =>
    (exp.results ?? []).find((r) => r.index === index)?.views;

  return (
    <div>
      <PageHeader
        title="A/B Title Experiments"
        subtitle="Automatic title rotation with a data-driven winner"
        actions={
          <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 220}}>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        }
      />

      {experiments.length === 0 && <EmptyState icon="🧪" title="No experiments yet" hint="Experiments are created automatically when videos are produced." />}

      {experiments.map((exp) => (
        <div className="card" key={exp.id}>
          <div className="row" style={{justifyContent: 'space-between'}}>
            <strong>Video #{exp.video_id}</strong>
            <span className={`badge ${exp.settled ? 'ok' : 'warn'}`}>
              {exp.settled ? `Winner: variant ${(exp.winner_index ?? 0) + 1}` : `Testing variant ${exp.current_index + 1}`}
            </span>
          </div>
          <table style={{marginTop: 8}}>
            <thead>
              <tr><th>#</th><th>Title</th><th>Views</th><th></th></tr>
            </thead>
            <tbody>
              {exp.variants.map((v, i) => (
                <tr key={i}>
                  <td>{i + 1}{i === exp.current_index && !exp.settled ? ' ▶' : ''}{exp.winner_index === i ? ' 🏆' : ''}</td>
                  <td>{v}</td>
                  <td>{viewsFor(exp, i) ?? '—'}</td>
                  <td>{!exp.settled && <button className="secondary" onClick={() => promote(exp, i)}>Promote</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
