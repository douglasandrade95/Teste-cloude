import { NavLink, Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Clapperboard, SlidersHorizontal } from 'lucide-react'

import { Editor } from './pages/Editor'
import { Integrations } from './pages/Integrations'

const links = [
  { to: '/editor', label: 'Editor', icon: Clapperboard },
  { to: '/integracoes', label: 'Integrações', icon: SlidersHorizontal },
]

function TopNav() {
  return (
    <nav className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <span className="font-display text-lg font-light tracking-wide text-bone-50">
          AutoVideoEditor
        </span>

        <div className="flex gap-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition ${
                  isActive
                    ? 'bg-gold-400/10 text-gold-300'
                    : 'text-bone-300 hover:text-bone-50'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}

export function App() {
  return (
    <Router>
      <TopNav />
      <Routes>
        <Route path="/editor" element={<Editor />} />
        <Route path="/integracoes" element={<Integrations />} />
        <Route path="*" element={<Navigate to="/editor" replace />} />
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#161514',
            color: '#f2ede5',
            border: '1px solid rgba(201,169,97,0.25)',
          },
        }}
      />
    </Router>
  )
}
