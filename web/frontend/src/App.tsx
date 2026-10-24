import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'

// Each page loads its own code; the chart library only downloads with the pages that draw charts.
const Gasto = lazy(() => import('./pages/Gasto.tsx'))
const Impuestos = lazy(() => import('./pages/Impuestos.tsx'))
const Inflacion = lazy(() => import('./pages/Inflacion.tsx'))
const Fuentes = lazy(() => import('./pages/Fuentes.tsx'))

const PAGES = [
  { to: '/', label: 'Gasto' },
  { to: '/impuestos', label: 'Impuestos' },
  { to: '/inflacion', label: 'Inflación' },
  { to: '/fuentes', label: 'Fuentes' },
]

export default function App() {
  return (
    <div className="layout">
      <header className="topbar">
        <NavLink to="/" className="brand">¿A dónde va?</NavLink>
        <nav className="nav" aria-label="Secciones">
          {PAGES.map((p) => (
            <NavLink key={p.to} to={p.to} end={p.to === '/'}>{p.label}</NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Suspense fallback={<p className="muted">Cargando…</p>}>
          <Routes>
            <Route path="/" element={<Gasto />} />
            <Route path="/impuestos" element={<Impuestos />} />
            <Route path="/inflacion" element={<Inflacion />} />
            <Route path="/fuentes" element={<Fuentes />} />
            <Route path="*" element={<p>Esta página no existe.</p>} />
          </Routes>
        </Suspense>
      </main>
      <footer>
        Datos oficiales de OPP, MEF e INE (Licencia de Datos Abiertos – Uruguay) y datasets compilados por{' '}
        <a href="https://github.com/juangcapo/adondeva">adondeva</a> (CC BY 4.0).
      </footer>
    </div>
  )
}
