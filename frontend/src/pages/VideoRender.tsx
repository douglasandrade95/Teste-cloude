import React, { useState } from 'react';
import { VideoRenderer } from '../components/VideoRenderer';

export const VideoRenderPage: React.FC = () => {
  const [renderedVideoUrl, setRenderedVideoUrl] = useState('');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-12">Video Rendering</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Renderer Panel */}
          <div className="lg:col-span-2">
            <VideoRenderer onRenderComplete={setRenderedVideoUrl} />
          </div>

          {/* Preview Panel */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">Preview</h3>
            {renderedVideoUrl ? (
              <div className="space-y-4">
                <video
                  src={renderedVideoUrl}
                  controls
                  className="w-full rounded-lg"
                />
                <a
                  href={renderedVideoUrl}
                  download
                  className="block w-full bg-green-600 text-white text-center font-semibold py-2 rounded-lg hover:bg-green-700"
                >
                  Download Video
                </a>
              </div>
            ) : (
              <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
                Rendered video preview will appear here
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
