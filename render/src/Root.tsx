import React from 'react';
import {Composition} from 'remotion';
import {Short} from './Short';
import {FPS, HEIGHT, WIDTH, shortSchema} from './types';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Short"
      component={Short}
      durationInFrames={30 * FPS}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      schema={shortSchema}
      defaultProps={{
        video_id: 0,
        duration: 30,
        audio_url: null,
        captions: [],
        visuals: [],
        hook: null,
        music_url: null,
        music_volume: 0.12,
      }}
      // Adjust the timeline length to match the narration duration.
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(1, Math.round((props.duration || 30) * FPS)),
      })}
    />
  );
};
