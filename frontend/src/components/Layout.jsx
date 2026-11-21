import { useEffect, useRef, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
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

export function Menu({ label = 'Weitere Aktionen', items }) {
  const [open, setOpen] = useState(false)
  const root = useRef(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e) => !root.current?.contains(e.target) && setOpen(false)
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="menu" ref={root}>
      <button
        className="icon-btn"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <Icon name="more" />
      </button>
      {open && (
        <div className="menu-list" role="menu">
          {items.filter(Boolean).map((item) => (
            <button
              key={item.label}
              role="menuitem"
              className={item.danger ? 'is-danger' : ''}
              onClick={() => {
                setOpen(false)
                item.onClick()
              }}
            >
              <Icon name={item.icon} size={16} />
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function Notice({ text, onClose }) {
  if (!text) return null
  return (
    <div className="notice" role="status">
      <span>{text}</span>
      <button className="icon-btn icon-btn-small" aria-label="Schließen" onClick={onClose}>
        <Icon name="close" size={16} />
      </button>
    </div>
  )
}

export default function Layout() {
  const grades = useLocation().pathname.startsWith('/grades')
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand" aria-label="Startseite">
          <Logo />
        </Link>
        <nav className="tabs" aria-label="Bereiche">
          <Link to="/" className={grades ? 'tab' : 'tab active'} aria-current={grades ? undefined : 'page'}>Lernen</Link>
          <Link to="/grades" className={grades ? 'tab active' : 'tab'} aria-current={grades ? 'page' : undefined}>Noten</Link>
        </nav>
        <ThemeToggle />
      </header>
      <main className="page">
        <Outlet />
      </main>
    </>
  )
}
