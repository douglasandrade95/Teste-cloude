# AutoVideoEditor - Frontend

React + TypeScript frontend for AI video editing application.

## Design Philosophy

- **Apple-inspired simplicity** - Minimal, elegant interface
- **Notion-like refinement** - Spacious, breathing design
- **CapCut premium feel** - Fast, responsive interactions
- **Mobile-first** - Optimized for all screen sizes

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview
```

## Architecture

```
src/
├── pages/
│   └── Editor.tsx         # Main editor interface
├── components/            # Reusable components (Phase 2)
├── services/              # API calls (Phase 2)
├── hooks/                 # Custom React hooks (Phase 2)
├── types/                 # TypeScript types
├── styles/                # Global styles
└── main.tsx               # App entry point
```

## Key Technologies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first styling
- **Zustand** - State management (Phase 2)
- **Axios** - HTTP client
- **React Hot Toast** - Notifications
- **Lucide React** - Icons

## Features (MVP)

1. **Upload Section**
   - Video file selection
   - Vibe/atmosphere selection
   - File validation

2. **Analysis Display**
   - Emotional analysis results
   - Recommended settings
   - Color palette suggestions

3. **Progress Tracking**
   - Real-time editing progress
   - Status updates
   - Download ready notification

## Component Structure (Phase 2)

```
Editor (main page)
├── UploadZone
├── VibeSelector
├── AnalysisPanel
├── ProgressBar
└── DownloadButton
```

## Styling

- **TailwindCSS** for utilities
- **Dark theme** (slate/blue/purple palette)
- **Responsive** grid system
- **Smooth transitions** and animations

## Environment Variables

```
VITE_API_URL=http://localhost:8000
VITE_UPLOAD_MAX_SIZE=2147483648
```

## Performance

- Code splitting ready
- Image optimization (lazy loading planned)
- Efficient re-renders with React.memo (Phase 2)
- Gzip compression enabled

## Next Phase (Phase 2)

- Drag-drop functionality
- Advanced settings panel
- Reference image upload
- Real-time preview
- Sharing integration
