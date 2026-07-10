import {useEffect, useState} from 'react';
import {Channel, api} from '../api';
import {PageHeader, useToast} from '../components/ui';

interface AffiliateLink {
  keyword: string;
  url: string;
  label: string;
}

interface Monetization {
  channel_id: number;
  affiliate_links: AffiliateLink[] | null;
  sponsor_active: boolean;
  sponsor_name: string | null;
  sponsor_script: string | null;
  sponsor_placement: string;
  cta_text: string | null;
  lead_url: string | null;
  pinned_comment: string | null;
}

export default function Monetize() {
  const {push} = useToast();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [m, setM] = useState<Monetization | null>(null);

  useEffect(() => {
    api.get<Channel[]>('/channels').then(({data}) => {
      setChannels(data);
      if (data.length) setSelected(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (selected == null) return;
    api.get<Monetization>(`/channels/${selected}/monetization`).then(({data}) => {
      setM({...data, affiliate_links: data.affiliate_links ?? []});
    });
  }, [selected]);

  const save = async () => {
    if (selected == null || !m) return;
    await api.put(`/channels/${selected}/monetization`, m);
    push('Monetization saved.', 'success');
  };

  const addLink = () => {
    if (!m) return;
    setM({...m, affiliate_links: [...(m.affiliate_links ?? []), {keyword: '', url: '', label: ''}]});
  };
  const updateLink = (i: number, field: keyof AffiliateLink, value: string) => {
    if (!m) return;
    const links = [...(m.affiliate_links ?? [])];
    links[i] = {...links[i], [field]: value};
    setM({...m, affiliate_links: links});
  };
  const removeLink = (i: number) => {
    if (!m) return;
    setM({...m, affiliate_links: (m.affiliate_links ?? []).filter((_, j) => j !== i)});
  };

  return (
    <div>
      <PageHeader
        title="Monetization"
        subtitle="Affiliate links, sponsor reads, and CTAs per channel"
        actions={
          <select value={selected ?? ''} onChange={(e) => setSelected(Number(e.target.value))} style={{width: 220}}>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        }
      />

      {m && (
        <>
          <div className="card">
            <h3>Affiliate links</h3>
            <p className="stat-label">Links with a keyword are added only when that keyword appears in the video; blank keyword = always included.</p>
            {(m.affiliate_links ?? []).map((l, i) => (
              <div className="row" key={i} style={{marginTop: 8}}>
                <input placeholder="keyword" value={l.keyword} onChange={(e) => updateLink(i, 'keyword', e.target.value)} />
                <input placeholder="label" value={l.label} onChange={(e) => updateLink(i, 'label', e.target.value)} />
                <input placeholder="https://..." value={l.url} onChange={(e) => updateLink(i, 'url', e.target.value)} />
                <button className="secondary" onClick={() => removeLink(i)}>✕</button>
              </div>
            ))}
            <div style={{marginTop: 10}}><button className="secondary" onClick={addLink}>+ Add link</button></div>
          </div>

          <div className="card">
            <h3>Sponsorship ad-read</h3>
            <label className="row" style={{gap: 8}}>
              <input type="checkbox" style={{width: 'auto'}} checked={m.sponsor_active} onChange={(e) => setM({...m, sponsor_active: e.target.checked})} />
              <span>Active (voiced into the video)</span>
            </label>
            <label>Sponsor name</label>
            <input value={m.sponsor_name ?? ''} onChange={(e) => setM({...m, sponsor_name: e.target.value})} />
            <label>Ad-read script</label>
            <textarea rows={3} value={m.sponsor_script ?? ''} onChange={(e) => setM({...m, sponsor_script: e.target.value})} />
            <label>Placement</label>
            <select value={m.sponsor_placement} onChange={(e) => setM({...m, sponsor_placement: e.target.value})}>
              <option value="intro">Intro</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div className="card">
            <h3>CTA &amp; lead magnet</h3>
            <label>CTA text</label>
            <input value={m.cta_text ?? ''} onChange={(e) => setM({...m, cta_text: e.target.value})} placeholder="Join my free newsletter" />
            <label>Lead / product URL</label>
            <input value={m.lead_url ?? ''} onChange={(e) => setM({...m, lead_url: e.target.value})} placeholder="https://..." />
            <label>Pinned comment (optional override)</label>
            <input value={m.pinned_comment ?? ''} onChange={(e) => setM({...m, pinned_comment: e.target.value})} />
          </div>

          <button onClick={save}>Save monetization</button>
        </>
      )}
    </div>
  );
}
