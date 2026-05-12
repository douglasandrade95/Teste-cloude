# Remotion Integration Setup

## Overview
This document describes the Remotion integration for video rendering in the AutoVideoEditor project.

## What is Remotion?
Remotion is a React framework for creating and composing videos programmatically. It allows you to:
- Create video compositions using React components
- Render videos server-side or in the browser
- Export high-quality MP4 videos
- Compose complex animations and effects

## Architecture

### Frontend Structure
```
frontend/src/remotion/
├── Root.tsx                    # Remotion root component with composition registry
├── index.ts                    # Export point
└── compositions/
    └── VideoTemplate.tsx       # Video template composition
```

### Backend Structure
```
backend/app/services/
└── remotion_renderer.py        # Remotion render job management

backend/app/api/
└── routes.py                   # Render API endpoints
```

## API Endpoints

### 1. Create Render Job
```
POST /api/v1/render
```
**Request:**
```json
{
  "composition_id": "VideoTemplate",
  "duration_in_frames": 300,
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "props": {
    "videoUrl": "https://example.com/video.mp4",
    "audioUrl": "https://example.com/audio.mp3",
    "title": "My Video",
    "subtitle": "Subtitle here",
    "duration": 10
  }
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "url": null
}
```

### 2. Get Job Status
```
GET /api/v1/render/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing", // or "completed", "failed", "cancelled"
  "url": "https://example.com/videos/{job_id}.mp4"
}
```

### 3. Cancel Job
```
DELETE /api/v1/render/{job_id}
```

### 4. List All Jobs
```
GET /api/v1/render-jobs
```

## Creating Custom Compositions

### Example: Simple Text Overlay
```tsx
import { AbsoluteFill, Text } from 'remotion';

export const TextOverlay = ({ text, fontSize = 60 }) => (
  <AbsoluteFill style={{ backgroundColor: '#000' }}>
    <Text style={{ fontSize, color: '#fff', textAlign: 'center' }}>
      {text}
    </Text>
  </AbsoluteFill>
);
```

### Register in Root.tsx
```tsx
<Composition
  id="TextOverlay"
  component={TextOverlay}
  durationInFrames={300}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{ text: 'Hello World' }}
/>
```

## Usage in Frontend

### VideoRenderer Component
The `VideoRenderer` component provides a UI for rendering videos:

```tsx
import { VideoRenderer } from '@/components/VideoRenderer';

<VideoRenderer onRenderComplete={(videoUrl) => {
  console.log('Video ready:', videoUrl);
}} />
```

### Remotion Service
Use the `remotionService` for direct API calls:

```tsx
import { remotionService } from '@/services/remotionService';

const response = await remotionService.renderVideo({
  compositionId: 'VideoTemplate',
  durationInFrames: 300,
  fps: 30,
  width: 1080,
  height: 1920,
  props: { videoUrl: '...' },
});
```

## Configuration

### Frontend Config (remotion.config.ts)
- Video format: PNG
- H.264 preset: faster
- Bitrate: 8M
- Concurrency: 4 processes
- Max retries: 3

### Environment Variables
Add to `.env`:
```
VITE_API_URL=http://localhost:8000
```

## Development Workflow

### 1. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Create Render Job
1. Navigate to `/render` route
2. Fill in video/audio URLs
3. Add title and subtitle (optional)
4. Click "Start Rendering"
5. Monitor job status

## Advanced Features

### Custom Sequences
```tsx
import { Sequence } from 'remotion';

<Sequence from={0} durationInFrames={150}>
  <FirstScene />
</Sequence>
<Sequence from={150} durationInFrames={150}>
  <SecondScene />
</Sequence>
```

### Interpolation
```tsx
import { interpolate, useCurrentFrame } from 'remotion';

const frame = useCurrentFrame();
const opacity = interpolate(frame, [0, 30], [0, 1]);
```

### Dynamic Props
```tsx
<Composition
  id="Dynamic"
  component={MyComponent}
  durationInFrames={300}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{...}}
  calculateMetadata={({ fps, durationInFrames }) => ({
    fps,
    durationInFrames,
  })}
/>
```

## Troubleshooting

### Video Rendering Fails
- Check video URL is accessible
- Verify composition ID exists in Root.tsx
- Check props match composition interface

### Slow Rendering
- Reduce `width` and `height` for testing
- Lower `fps` (24 is acceptable for social media)
- Check FFmpeg installation

### CORS Issues
- Ensure backend CORS is properly configured
- Update `VITE_API_URL` environment variable

## Next Steps
1. Implement actual FFmpeg rendering in backend
2. Add job persistence (database)
3. Create additional compositions (transitions, effects)
4. Add real-time job progress tracking
5. Implement video caching

## Resources
- [Remotion Documentation](https://www.remotion.dev/docs)
- [API Reference](https://www.remotion.dev/docs/remotion)
- [Examples](https://github.com/remotion-dev/remotion/tree/main/apps/examples)
