import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Editor } from './pages/Editor'
import { ImageGenerator } from './pages/ImageGenerator'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <nav className="flex gap-4 justify-center py-4 bg-slate-950 border-b border-slate-800">
        <Link to="/" className="text-slate-300 hover:text-white font-medium">
          Editor de Vídeo
        </Link>
        <Link
          to="/gerar-imagem"
          className="text-slate-300 hover:text-white font-medium"
        >
          Gerador de Imagens
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Editor />} />
        <Route path="/gerar-imagem" element={<ImageGenerator />} />
      </Routes>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Toaster position="top-right" />
    <App />
  </React.StrictMode>,
)
