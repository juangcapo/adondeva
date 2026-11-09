import { lazy, Suspense, useEffect, useRef } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { track } from './api.ts'

// Each page loads its own code; the chart library only downloads with the pages that draw charts.
const Gasto = lazy(() => import('./pages/Gasto.tsx'))
const Recaudacion = lazy(() => import('./pages/Recaudacion.tsx'))
const Impuestos = lazy(() => import('./pages/Impuestos.tsx'))
const Fuentes = lazy(() => import('./pages/Fuentes.tsx'))
const Admin = lazy(() => import('./pages/Admin.tsx'))
const Apoyar = lazy(() => import('./pages/Apoyar.tsx'))
const Noticias = lazy(() => import('./pages/Noticias.tsx'))
const NotaPropia = lazy(() => import('./pages/Noticias.tsx').then((m) => ({ default: m.NotaPropia })))
const NoticiasAdmin = lazy(() => import('./pages/NoticiasAdmin.tsx'))
const GastosRecientes = lazy(() => import('./pages/GastosRecientes.tsx'))
const GastoCasoPage = lazy(() => import('./pages/GastosRecientes.tsx').then((m) => ({ default: m.GastoCasoPage })))
const GastosAdmin = lazy(() => import('./pages/GastosAdmin.tsx'))

/** One page view per route change; the referrer only on arrival, and only from another site. */
function usePageViews() {
  const { pathname, search } = useLocation()
  const first = useRef(true)
  useEffect(() => {
    if (pathname.startsWith('/admin')) return
    let referrer: string | undefined
    if (first.current && document.referrer) {
      try {
        if (new URL(document.referrer).host !== location.host) referrer = document.referrer
      } catch {
        // malformed referrer: leave it out
      }
    }
    first.current = false
    track('pagina', pathname + search, { referrer })
  }, [pathname, search])
}

const PAGES = [
  { to: '/', label: 'Gasto' },
  { to: '/recaudacion', label: 'Recaudación' },
  { to: '/impuestos', label: 'Impuestos' },
  { to: '/gastos-recientes', label: 'Gastos recientes' },
  // { to: '/noticias', label: 'Noticias' }, // oculta por ahora; la ruta sigue andando
  { to: '/fuentes', label: 'Fuentes' },
]

export default function App() {
  usePageViews()
  return (
    <div className="layout">
      <header className="topbar">
        <NavLink to="/" className="brand">¿A dónde va?</NavLink>
        <nav className="nav" aria-label="Secciones">
          {PAGES.map((p) => (
            <NavLink key={p.to} to={p.to} end={p.to === '/'}>{p.label}</NavLink>
          ))}
        </nav>
        <NavLink to="/apoyar" className="apoyar">♥ Apoyá el sitio</NavLink>
      </header>
      <main>
        <Suspense fallback={<p className="muted">Cargando…</p>}>
          <Routes>
            <Route path="/" element={<Gasto />} />
            <Route path="/recaudacion" element={<Recaudacion />} />
            <Route path="/impuestos" element={<Impuestos />} />
            <Route path="/fuentes" element={<Fuentes />} />
            <Route path="/apoyar" element={<Apoyar />} />
            <Route path="/noticias" element={<Noticias />} />
            <Route path="/noticias/:slug" element={<NotaPropia />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/admin/noticias" element={<NoticiasAdmin />} />
            <Route path="/gastos-recientes" element={<GastosRecientes />} />
            <Route path="/gastos-recientes/:slug" element={<GastoCasoPage />} />
            <Route path="/admin/gastos-recientes" element={<GastosAdmin />} />
            <Route path="*" element={<p>Esta página no existe.</p>} />
          </Routes>
        </Suspense>
      </main>
      <footer>
        Datos oficiales de OPP, MEF, INE y DGI (Licencia de Datos Abiertos – Uruguay) y datasets compilados por{' '}
        <a href="https://github.com/juangcapo/adondeva">adondeva</a> (CC BY 4.0).
        {' '}Registramos de forma anónima las visitas y consultas, sin cookies ni direcciones IP, para saber cómo se usa el sitio.
        {' '}¿Te sirve? <NavLink to="/apoyar">Apoyá el sitio</NavLink>.
      </footer>
    </div>
  )
}
