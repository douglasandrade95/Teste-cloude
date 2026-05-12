import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Editor } from './pages/Editor'
import { VideoRenderPage } from './pages/VideoRender'
import './index.css'

const App: React.FC = () => (
  <Router>
    <Routes>
      <Route path="/" element={<Navigate to="/editor" replace />} />
      <Route path="/editor" element={<Editor />} />
      <Route path="/render" element={<VideoRenderPage />} />
    </Routes>
  </Router>
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
