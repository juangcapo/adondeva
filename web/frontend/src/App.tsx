import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'

// Each page loads its own code; the chart library only downloads with the pages that draw charts.
const Gasto = lazy(() => import('./pages/Gasto.tsx'))
const Recaudacion = lazy(() => import('./pages/Recaudacion.tsx'))
const Impuestos = lazy(() => import('./pages/Impuestos.tsx'))
const Fuentes = lazy(() => import('./pages/Fuentes.tsx'))

const PAGES = [
  { to: '/', label: 'Gasto' },
  { to: '/recaudacion', label: 'Recaudación' },
  { to: '/impuestos', label: 'Impuestos' },
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
            <Route path="/recaudacion" element={<Recaudacion />} />
            <Route path="/impuestos" element={<Impuestos />} />
            <Route path="/fuentes" element={<Fuentes />} />
            <Route path="*" element={<p>Esta página no existe.</p>} />
          </Routes>
        </Suspense>
      </main>
      <footer>
        Datos oficiales de OPP, MEF, INE y DGI (Licencia de Datos Abiertos – Uruguay) y datasets compilados por{' '}
        <a href="https://github.com/juangcapo/adondeva">adondeva</a> (CC BY 4.0).
      </footer>
    </div>
  )
}
