import React from 'react';
import { Composition } from 'remotion';
import { VideoTemplate } from './compositions/VideoTemplate';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="VideoTemplate"
        component={VideoTemplate}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoUrl: 'https://example.com/video.mp4',
          duration: 10,
        }}
      />
    </>
  );
};
