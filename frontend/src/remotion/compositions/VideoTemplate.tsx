import React from 'react';
import { Composition, Img, Video, Audio, AbsoluteFill, useVideoConfig } from 'remotion';

interface VideoTemplateProps {
  videoUrl: string;
  audioUrl?: string;
  title?: string;
  subtitle?: string;
  duration: number;
}

export const VideoTemplate: React.FC<VideoTemplateProps> = ({
  videoUrl,
  audioUrl,
  title,
  subtitle,
  duration,
}) => {
  const { width, height, fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Main Video Background */}
      <Video src={videoUrl} />

      {/* Audio Layer */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Text Overlay */}
      {(title || subtitle) && (
        <AbsoluteFill
          style={{
            justifyContent: 'center',
            alignItems: 'center',
            flexDirection: 'column',
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
          }}
        >
          {title && (
            <div
              style={{
                fontSize: 72,
                fontWeight: 'bold',
                color: '#fff',
                textAlign: 'center',
                marginBottom: 20,
              }}
            >
              {title}
            </div>
          )}
          {subtitle && (
            <div
              style={{
                fontSize: 36,
                color: '#ddd',
                textAlign: 'center',
              }}
            >
              {subtitle}
            </div>
          )}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
