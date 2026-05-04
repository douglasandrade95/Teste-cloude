import React, { useState } from 'react';
import { Composition } from 'remotion';

export const VideoEditor = () => {
  const [clips, setClips] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(3);

  const addClip = (clip) => {
    setClips([...clips, { id: Date.now(), ...clip }]);
  };

  const removeClip = (id) => {
    setClips(clips.filter(clip => clip.id !== id));
  };

  const updateClip = (id, updates) => {
    setClips(clips.map(clip => clip.id === id ? { ...clip, ...updates } : clip));
  };

  return (
    <div className="video-editor">
      <div className="editor-header">
        <h1>Editor de Vídeos</h1>
        <div className="timeline-info">
          <span>Duração: {duration}s</span>
          <span>Tempo: {currentTime.toFixed(2)}s</span>
        </div>
      </div>

      <div className="editor-layout">
        {/* Preview */}
        <div className="preview-section">
          <div className="video-preview">
            <Composition
              id="video-preview"
              component={VideoPreview}
              durationInFrames={duration * 30}
              fps={30}
              width={1280}
              height={720}
              defaultProps={{ clips }}
            />
          </div>
        </div>

        {/* Timeline */}
        <div className="timeline-section">
          <div className="timeline">
            <TimelineTrack clips={clips} duration={duration} currentTime={currentTime} />
          </div>
          <input
            type="range"
            min="0"
            max={duration}
            step="0.01"
            value={currentTime}
            onChange={(e) => setCurrentTime(parseFloat(e.target.value))}
            className="timeline-scrubber"
          />
        </div>

        {/* Controls */}
        <div className="controls-section">
          <button onClick={() => addClip({ type: 'text', text: 'Novo texto', duration: 1 })}>
            + Adicionar Texto
          </button>
          <button onClick={() => addClip({ type: 'image', duration: 2 })}>
            + Adicionar Imagem
          </button>
          <button onClick={() => addClip({ type: 'video', duration: 3 })}>
            + Adicionar Vídeo
          </button>
        </div>

        {/* Clips List */}
        <div className="clips-section">
          <h3>Clipes</h3>
          <ul className="clips-list">
            {clips.map(clip => (
              <li key={clip.id} className="clip-item">
                <div className="clip-info">
                  <span className="clip-type">{clip.type}</span>
                  <span className="clip-duration">{clip.duration}s</span>
                </div>
                <button onClick={() => removeClip(clip.id)} className="clip-remove">
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export const VideoPreview = ({ clips }) => {
  return (
    <div className="video-canvas">
      {clips.map((clip, index) => (
        <div
          key={clip.id}
          className={`clip-render ${clip.type}`}
          style={{
            position: 'absolute',
            zIndex: index,
          }}
        >
          {clip.type === 'text' && <p>{clip.text}</p>}
          {clip.type === 'image' && <img src={clip.src} alt="clip" />}
          {clip.type === 'video' && <video src={clip.src} />}
        </div>
      ))}
    </div>
  );
};

const TimelineTrack = ({ clips, duration, currentTime }) => {
  return (
    <div className="timeline-track">
      <div
        className="playhead"
        style={{
          left: `${(currentTime / duration) * 100}%`,
        }}
      />
      {clips.map(clip => (
        <div
          key={clip.id}
          className="timeline-clip"
          style={{
            left: `${(clip.startTime || 0) / duration * 100}%`,
            width: `${clip.duration / duration * 100}%`,
          }}
        >
          <span>{clip.type}</span>
        </div>
      ))}
    </div>
  );
};

export default VideoEditor;
