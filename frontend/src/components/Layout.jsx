import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import Icon from './Icon.jsx'

export function Logo() {
  return (
    <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
      <rect
        x="9" y="6" width="16" height="12" rx="2.5"
        fill="none" stroke="currentColor" strokeWidth="2" transform="rotate(8 17 12)"
      />
      <rect x="7" y="13" width="16" height="12" rx="2.5" fill="var(--accent)" />
    </svg>
  )
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light')
  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem('theme', next)
    } catch {
    }
    setTheme(next)
  }
  return (
    <button
      className="icon-btn"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Helles Design' : 'Dunkles Design'}
      data-tip={theme === 'dark' ? 'Helles Design' : 'Dunkles Design'}
      data-tip-align="end"
    >
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
    </button>
  )
}

export function Breadcrumbs({ items }) {
  return (
    <nav className="crumbs" aria-label="Brotkrumen">
      <ol>
        {items.map((item, i) => (
          <li key={i}>
            {item.to ? <Link to={item.to}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export default function Layout() {
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          <Logo />
          <span>Karteikarten</span>
        </Link>
        <nav className="topnav">
          <NavLink to="/grades" className="btn btn-ghost btn-small">Noten</NavLink>
          <ThemeToggle />
        </nav>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </>
  )
}
