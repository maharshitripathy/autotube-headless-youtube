import {useEffect, useMemo, useState} from 'react';
import {Channel, VideoOut, api} from '../api';
import {Drawer, EmptyState, PageHeader, SkeletonCards, StatusBadge, useToast} from '../components/ui';

interface Detail {
  video: VideoOut;
  media: {video_url: string | null; thumbnail_url: string | null};
  distributions: {platform: string; status: string; caption: string | null; download_url: string | null; external_id: string | null}[];
}

const STATUSES = ['all', 'published', 'scheduled', 'ready', 'rendering', 'draft', 'failed'];

function VideoCard({video, onOpen}: {video: VideoOut; onOpen: () => void}) {
  const [media, setMedia] = useState<{img: string | null; vid: string | null}>({img: null, vid: null});
  useEffect(() => {
    api.get(`/videos/${video.id}/media`)
      .then(({data}) => setMedia({img: data.thumbnail_url, vid: data.video_url}))
      .catch(() => undefined);
  }, [video.id]);
  return (
    <div className="card hover" style={{cursor: 'pointer', padding: 10}} onClick={onOpen}>
      {media.img ? (
        <img src={media.img} className="thumb" />
      ) : media.vid ? (
        <video src={media.vid} className="thumb" muted preload="metadata" />
      ) : (
        <div className="thumb" style={{display: 'grid', placeItems: 'center', color: 'var(--muted)'}}>🎬</div>
      )}
      <div style={{marginTop: 8}}>
        <div style={{fontSize: 13.5, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
          {video.title || video.topic || `Video #${video.id}`}
        </div>
        <div className="spread" style={{marginTop: 6}}>
          <StatusBadge status={video.status} />
          {video.qa_passed === false && <span className="badge bad">QA</span>}
        </div>
      </div>
    </div>
  );
}

export default function Library() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState<number | 'all'>('all');
  const [status, setStatus] = useState('all');
  const [query, setQuery] = useState('');
  const [videos, setVideos] = useState<VideoOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => setChannels(data));
  }, []);

  const load = () => {
    setLoading(true);
    const params = channelId === 'all' ? {} : {channel_id: channelId};
    api.get<VideoOut[]>('/videos', {params}).then(({data}) => setVideos(data)).finally(() => setLoading(false));
  };

  useEffect(load, [channelId]);

  const open = async (id: number) => {
    setDrawerOpen(true);
    setDetail(null);
    const {data} = await api.get<Detail>(`/videos/${id}/detail`);
    setDetail(data);
  };

  const regenerateThumb = async () => {
    if (!detail) return;
    setRegenerating(true);
    try {
      const {data} = await api.post(`/videos/${detail.video.id}/thumbnail`);
      setDetail({...detail, media: {...detail.media, thumbnail_url: data.thumbnail_url}});
      push('Thumbnail regenerated.', 'success');
    } catch {
      push('Thumbnail generation failed.', 'error');
    } finally {
      setRegenerating(false);
    }
  };

  const filtered = useMemo(() => {
    return videos.filter((v) => {
      if (status !== 'all' && v.status !== status) return false;
      if (query && !`${v.title ?? ''} ${v.topic ?? ''}`.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [videos, status, query]);

  const channelName = (id: number) => channels.find((c) => c.id === id)?.title ?? `Channel ${id}`;

  return (
    <div>
      <PageHeader
        title="Video Library"
        subtitle={`${filtered.length} video${filtered.length === 1 ? '' : 's'}`}
        actions={
          <>
            <select value={channelId} onChange={(e) => setChannelId(e.target.value === 'all' ? 'all' : Number(e.target.value))} style={{width: 180}}>
              <option value="all">All channels</option>
              {channels.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)} style={{width: 140}}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input placeholder="Search…" value={query} onChange={(e) => setQuery(e.target.value)} style={{width: 180}} />
          </>
        }
      />

      {loading ? (
        <SkeletonCards count={8} />
      ) : filtered.length === 0 ? (
        <EmptyState icon="🎬" title="No videos yet" hint="Run a channel pipeline to produce your first Short." />
      ) : (
        <div className="grid wide">
          {filtered.map((v) => <VideoCard key={v.id} video={v} onOpen={() => open(v.id)} />)}
        </div>
      )}

      <Drawer open={drawerOpen} title={detail?.video.title ?? 'Video'} onClose={() => setDrawerOpen(false)} width={460}>
        {!detail ? (
          <div className="loading-row"><span className="spinner" /> <span className="muted">Loading…</span></div>
        ) : (
          <>
            {detail.media.video_url && <video src={detail.media.video_url} controls className="thumb" style={{maxHeight: 420, width: 'auto', margin: '0 auto', display: 'block'}} />}
            <div style={{marginTop: 12}}>
              <div className="spread">
                <h4 style={{margin: 0}}>Thumbnail</h4>
                <button className="secondary" onClick={regenerateThumb} disabled={regenerating}>
                  {regenerating ? 'Generating…' : 'Regenerate'}
                </button>
              </div>
              {detail.media.thumbnail_url ? (
                <img src={detail.media.thumbnail_url} style={{width: '100%', borderRadius: 10, marginTop: 8}} />
              ) : (
                <p className="muted" style={{fontSize: 13}}>No thumbnail yet.</p>
              )}
            </div>
            <div className="spread" style={{marginTop: 12}}>
              <StatusBadge status={detail.video.status} />
              <span className="muted" style={{fontSize: 12}}>{channelName(detail.video.channel_id)}</span>
            </div>
            {detail.video.youtube_video_id && (
              <p style={{marginTop: 10}}>
                <a href={`https://youtube.com/watch?v=${detail.video.youtube_video_id}`} target="_blank" rel="noreferrer">▶ Open on YouTube</a>
              </p>
            )}
            <h4 style={{margin: '14px 0 4px'}}>Description</h4>
            <p className="muted" style={{fontSize: 13, whiteSpace: 'pre-wrap'}}>{detail.video.description || '—'}</p>
            {detail.video.tags && detail.video.tags.length > 0 && (
              <div className="row wrap" style={{marginTop: 10}}>
                {detail.video.tags.map((t: string, i: number) => <span key={i} className="badge">{t}</span>)}
              </div>
            )}
            {detail.video.qa_notes && detail.video.qa_notes.length > 0 && (
              <>
                <h4 style={{margin: '14px 0 4px'}}>QA notes</h4>
                {detail.video.qa_notes.map((n: string, i: number) => <div key={i} className="stat-label">• {n}</div>)}
              </>
            )}
            {detail.distributions.length > 0 && (
              <>
                <h4 style={{margin: '14px 0 4px'}}>Cross-posts</h4>
                {detail.distributions.map((d, i) => (
                  <div key={i} className="spread" style={{padding: '6px 0'}}>
                    <span>{d.platform}</span>
                    <StatusBadge status={d.status} />
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
}
