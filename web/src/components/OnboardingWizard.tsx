import {useEffect, useState} from 'react';
import {Channel, api} from '../api';
import {Modal, useToast} from './ui';

interface Preset {
  id: string;
  name: string;
  niche: string;
  uploads_per_day: number;
  cta_text?: string;
}

/**
 * Guided first-run setup. Because OAuth navigates away and returns to
 * /channels?connected=1, the wizard can be opened directly at the "configure"
 * step for the newly connected channel.
 */
export function OnboardingWizard({
  open,
  onClose,
  channels,
  startStep = 'connect',
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  channels: Channel[];
  startStep?: 'connect' | 'configure';
  onDone: () => void;
}) {
  const {push} = useToast();
  const [step, setStep] = useState(startStep);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [channelId, setChannelId] = useState<number | null>(null);
  const [presetId, setPresetId] = useState('');
  const [uploads, setUploads] = useState(1);
  const [autonomous, setAutonomous] = useState(false);
  const [requireApproval, setRequireApproval] = useState(true);
  const [cta, setCta] = useState('');
  const [leadUrl, setLeadUrl] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) {
      setStep(startStep);
      api.get<Preset[]>('/bulk/presets').then(({data}) => setPresets(data)).catch(() => undefined);
    }
  }, [open, startStep]);

  useEffect(() => {
    if (channels.length && channelId == null) setChannelId(channels[channels.length - 1].id);
  }, [channels]);

  const connect = async () => {
    const {data} = await api.get('/auth/youtube/start');
    window.location.href = data.authorization_url;
  };

  const finish = async () => {
    if (channelId == null) return;
    setBusy(true);
    try {
      if (presetId) {
        await api.post('/bulk/presets/apply', {channel_ids: [channelId], preset_id: presetId});
      }
      await api.patch(`/channels/${channelId}`, {
        uploads_per_day: uploads,
        autonomous,
        require_approval: requireApproval,
      });
      if (cta || leadUrl) {
        await api.put(`/channels/${channelId}/monetization`, {
          cta_text: cta || null,
          lead_url: leadUrl || null,
        });
      }
      push('Channel configured — you are ready to go!', 'success');
      onDone();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  const preset = presets.find((p) => p.id === presetId);

  return (
    <Modal open={open} title="Set up your channel" onClose={onClose} width={560}>
      {step === 'connect' ? (
        <>
          <p className="muted" style={{marginTop: 0}}>
            Connect an existing YouTube channel via Google. AutoTube can’t create channels
            (YouTube policy), but it fully automates any channel you connect.
          </p>
          <ol className="muted" style={{fontSize: 13.5, lineHeight: 1.8}}>
            <li>Sign in with the Google account that owns the channel</li>
            <li>Grant upload, analytics, and comment permissions</li>
            <li>You’ll return here to finish configuration</li>
          </ol>
          <div className="row" style={{marginTop: 16}}>
            <button onClick={connect}>Connect YouTube channel</button>
            {channels.length > 0 && (
              <button className="secondary" onClick={() => setStep('configure')}>Skip — configure existing</button>
            )}
          </div>
        </>
      ) : (
        <>
          <label>Channel</label>
          <select value={channelId ?? ''} onChange={(e) => setChannelId(Number(e.target.value))}>
            {channels.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
          </select>

          <label>Niche preset</label>
          <select value={presetId} onChange={(e) => { setPresetId(e.target.value); const p = presets.find((x) => x.id === e.target.value); if (p) { setUploads(p.uploads_per_day); setCta(p.cta_text ?? ''); } }}>
            <option value="">Choose a preset…</option>
            {presets.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          {preset && <p className="muted" style={{fontSize: 12.5, marginTop: 4}}>{preset.niche}</p>}

          <label>Uploads per day</label>
          <input type="number" min={1} max={12} value={uploads} onChange={(e) => setUploads(Number(e.target.value))} />

          <label>Call-to-action (optional)</label>
          <input value={cta} onChange={(e) => setCta(e.target.value)} placeholder="Follow for daily shorts" />
          <label>Lead / product URL (optional)</label>
          <input value={leadUrl} onChange={(e) => setLeadUrl(e.target.value)} placeholder="https://…" />

          <div className="row" style={{marginTop: 12, flexWrap: 'wrap'}}>
            <label className="row" style={{gap: 8, margin: 0}}>
              <input type="checkbox" style={{width: 'auto'}} checked={autonomous} onChange={(e) => setAutonomous(e.target.checked)} />
              <span>Fully autonomous</span>
            </label>
            <label className="row" style={{gap: 8, margin: 0}}>
              <input type="checkbox" style={{width: 'auto'}} checked={requireApproval} onChange={(e) => setRequireApproval(e.target.checked)} />
              <span>Require approval before publish</span>
            </label>
          </div>

          <div className="row" style={{marginTop: 18}}>
            <button onClick={finish} disabled={busy || channelId == null}>{busy ? 'Saving…' : 'Finish setup'}</button>
            <button className="secondary" onClick={onClose}>Cancel</button>
          </div>
        </>
      )}
    </Modal>
  );
}
