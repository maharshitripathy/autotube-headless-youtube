import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {ShortProps} from './types';
import {FPS} from './types';

/** Full-bleed visual with a subtle Ken Burns zoom for still images. */
const VisualLayer: React.FC<{visuals: ShortProps['visuals']; durationInFrames: number}> = ({
  visuals,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  if (visuals.length === 0) {
    return <AbsoluteFill style={{backgroundColor: '#0b0b0f'}} />;
  }
  const per = Math.ceil(durationInFrames / visuals.length);
  return (
    <>
      {visuals.map((v, i) => {
        const from = i * per;
        const local = frame - from;
        const scale = interpolate(local, [0, per], [1, 1.12], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <Sequence key={i} from={from} durationInFrames={per}>
            <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#000'}}>
              {v.type === 'stock_video' && v.url ? (
                <OffthreadVideo
                  src={v.url}
                  muted
                  style={{width: '100%', height: '100%', objectFit: 'cover'}}
                />
              ) : v.type === 'veo' && v.url ? (
                <OffthreadVideo
                  src={v.url}
                  muted
                  style={{width: '100%', height: '100%', objectFit: 'cover'}}
                />
              ) : v.url ? (
                <Img
                  src={v.url}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    transform: `scale(${scale})`,
                  }}
                />
              ) : null}
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </>
  );
};

/** Word-level captions highlighting the active word (TikTok style). */
const Captions: React.FC<{captions: ShortProps['captions']}> = ({captions}) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  // Show a small sliding window of words around the current time.
  const activeIdx = captions.findIndex((w) => t >= w.start && t <= w.end);
  const center = activeIdx >= 0 ? activeIdx : captions.findIndex((w) => t < w.start);
  if (center < 0) return null;
  const windowWords = captions.slice(Math.max(0, center - 2), center + 3);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 320,
      }}
    >
      <div
        style={{
          maxWidth: 900,
          textAlign: 'center',
          fontFamily: 'Liberation Sans, Arial, sans-serif',
          fontWeight: 800,
          fontSize: 76,
          lineHeight: 1.1,
          color: 'white',
          textShadow: '0 4px 24px rgba(0,0,0,0.8)',
        }}
      >
        {windowWords.map((w, i) => {
          const isActive = t >= w.start && t <= w.end;
          return (
            <span
              key={`${w.start}-${i}`}
              style={{
                color: isActive ? '#ffe14d' : 'white',
                margin: '0 8px',
                display: 'inline-block',
                transform: isActive ? 'scale(1.08)' : 'scale(1)',
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Short: React.FC<ShortProps> = ({audio_url, captions, visuals}) => {
  const {durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <VisualLayer visuals={visuals} durationInFrames={durationInFrames} />
      <Captions captions={captions} />
      {audio_url ? <Audio src={audio_url} /> : null}
    </AbsoluteFill>
  );
};
