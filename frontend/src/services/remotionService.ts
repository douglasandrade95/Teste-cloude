import axios from 'axios';

interface RenderVideoRequest {
  compositionId: string;
  durationInFrames: number;
  fps: number;
  width: number;
  height: number;
  props?: Record<string, unknown>;
}

interface RenderVideoResponse {
  jobId: string;
  status: string;
  url?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const remotionService = {
  async renderVideo(request: RenderVideoRequest): Promise<RenderVideoResponse> {
    try {
      const response = await axios.post<RenderVideoResponse>(
        `${API_BASE_URL}/api/render`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Error rendering video:', error);
      throw error;
    }
  },

  async getRenderStatus(jobId: string): Promise<RenderVideoResponse> {
    try {
      const response = await axios.get<RenderVideoResponse>(
        `${API_BASE_URL}/api/render/${jobId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting render status:', error);
      throw error;
    }
  },

  async cancelRender(jobId: string): Promise<void> {
    try {
      await axios.delete(`${API_BASE_URL}/api/render/${jobId}`);
    } catch (error) {
      console.error('Error canceling render:', error);
      throw error;
    }
  },
};
