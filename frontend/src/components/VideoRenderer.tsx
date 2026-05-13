import React, { useState } from 'react';
import { remotionService } from '../services/remotionService';
import toast from 'react-hot-toast';
import { FileUp, Play, Loader } from 'lucide-react';

interface VideoRendererProps {
  onRenderComplete?: (videoUrl: string) => void;
}

export const VideoRenderer: React.FC<VideoRendererProps> = ({ onRenderComplete }) => {
  const [isRendering, setIsRendering] = useState(false);
  const [videoUrl, setVideoUrl] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [title, setTitle] = useState('');
  const [subtitle, setSubtitle] = useState('');

  const handleRender = async () => {
    if (!videoUrl) {
      toast.error('Please provide a video URL');
      return;
    }

    setIsRendering(true);
    try {
      const response = await remotionService.renderVideo({
        compositionId: 'VideoTemplate',
        durationInFrames: 300,
        fps: 30,
        width: 1080,
        height: 1920,
        props: {
          videoUrl,
          audioUrl: audioUrl || undefined,
          title: title || undefined,
          subtitle: subtitle || undefined,
          duration: 10,
        },
      });

      toast.success(`Rendering started! Job ID: ${response.jobId}`);
      onRenderComplete?.(response.url || '');
    } catch (error) {
      toast.error('Failed to start rendering');
      console.error(error);
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">Video Renderer</h2>

      <div className="space-y-4">
        {/* Video URL Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Video URL
          </label>
          <input
            type="url"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://example.com/video.mp4"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Audio URL Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Audio URL (Optional)
          </label>
          <input
            type="url"
            value={audioUrl}
            onChange={(e) => setAudioUrl(e.target.value)}
            placeholder="https://example.com/audio.mp3"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Title Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Title (Optional)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Video Title"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Subtitle Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subtitle (Optional)
          </label>
          <input
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            placeholder="Video Subtitle"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Render Button */}
        <button
          onClick={handleRender}
          disabled={isRendering}
          className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isRendering ? (
            <>
              <Loader className="animate-spin" size={20} />
              Rendering...
            </>
          ) : (
            <>
              <Play size={20} />
              Start Rendering
            </>
          )}
        </button>
      </div>
    </div>
  );
};
