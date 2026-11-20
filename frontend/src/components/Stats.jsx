import { useState } from 'react'
import { Link } from 'react-router-dom'
import RichText from './RichText.jsx'

const GROUPS = [
  {
    key: 'due',
    label: 'Fällig',
    color: 'var(--c-orange)',
    hint: 'Jetzt dran: neue Karten und solche, die wieder fällig sind',
  },
  {
    key: 'learned',
    label: 'Gelernt',
    color: 'var(--c-yellow)',
    hint: 'Im Plan, sitzt bis zur Klausur aber noch nicht sicher',
  },
  {
    key: 'consolidated',
    label: 'Gefestigt',
    color: 'var(--c-green)',
    hint: 'Sitzt voraussichtlich bis zur Klausur (ohne Klausur: stabil über mehrere Wochen)',
  },
]

export const totalCards = (stats) => stats.due + stats.learned + stats.consolidated

const percent = (n, total) => (total ? Math.round((n / total) * 100) : 0)
const cardsLabel = (n) => (n === 1 ? 'Karte' : 'Karten')
export const cardCount = (n) => `${n} ${cardsLabel(n)}`
const consolidatedPercent = (stats) => percent(stats.consolidated, totalCards(stats))

export const byName = (a, b) => a.name.localeCompare(b.name, 'de', { numeric: true, sensitivity: 'base' })

function Pie({ stats, size, thickness, active = null, onActive }) {
  const total = totalCards(stats)
  const parts = GROUPS.filter((s) => stats[s.key] > 0)
  const gap = parts.length > 1 ? 0.7 : 0
  let start = 0
  const summary = parts.map((s) => `${stats[s.key]} ${s.label}`).join(', ') || 'Keine Karten'

  return (
    <svg width={size} height={size} viewBox="0 0 42 42" role="img" aria-label={summary} className="pie">
      <circle cx="21" cy="21" r="15.915" fill="none" stroke="var(--surface-2)" strokeWidth={thickness} />
      {parts.map((s) => {
        const share = (stats[s.key] / total) * 100
        const length = Math.max(share - gap, 0.5)
        const offset = 25 - start - gap / 2
        start += share
        return (
          <circle
            key={s.key}
            cx="21" cy="21" r="15.915" fill="none"
            stroke={s.color}
            strokeWidth={active === s.key ? thickness + 1 : thickness}
            strokeDasharray={`${length} ${100 - length}`}
            strokeDashoffset={offset}
            opacity={active && active !== s.key ? 0.3 : 1}
            onPointerEnter={onActive && (() => onActive(s.key))}
            onPointerLeave={onActive && (() => onActive(null))}
          />
        )
      })}
    </svg>
  )
}

function StatePie({ stats }) {
  const [active, setActive] = useState(null)
  const shown = GROUPS.find((s) => s.key === active)
  const total = totalCards(stats)
  return (
    <div className="statepie">
      <div className="statepie-ring">
        <Pie stats={stats} size={168} thickness={5.5} active={active} onActive={setActive} />
        <div className="statepie-center">
          {shown ? (
            <>
              <b>{stats[shown.key]}</b>
              <span>{shown.label}<br />{percent(stats[shown.key], total)} %</span>
            </>
          ) : (
            <>
              <b>{consolidatedPercent(stats)}<small> %</small></b>
              <span>gefestigt</span>
            </>
          )}
        </div>
      </div>
      <ul className="legend">
        {GROUPS.map((s) => (
          <li
            key={s.key}
            title={s.hint}
            className={active && active !== s.key ? 'dim' : ''}
            onPointerEnter={() => setActive(s.key)}
            onPointerLeave={() => setActive(null)}
          >
            <i style={{ background: s.color }} />
            <span>{s.label}</span>
            <b>{stats[s.key]}</b>
            <em>{percent(stats[s.key], total)} %</em>
          </li>
        ))}
      </ul>
    </div>
  )
}

const dayFormat = new Intl.DateTimeFormat('de-DE', { weekday: 'short', day: 'numeric', month: 'short' })
const axisFormat = new Intl.DateTimeFormat('de-DE', { day: 'numeric', month: 'short' })
const examFormat = new Intl.DateTimeFormat('de-DE', { dateStyle: 'long', timeStyle: 'short' })
const localDate = (iso) => new Date(`${iso}T00:00`)

const DAY_MS = 24 * 60 * 60 * 1000
const startOfDay = (value) => {
  const day = new Date(value)
  day.setHours(0, 0, 0, 0)
  return day
}

export const formatExamDate = (iso) => `${examFormat.format(new Date(iso))} Uhr`

export function daysUntil(iso) {
  return Math.round((startOfDay(iso) - startOfDay(Date.now())) / DAY_MS)
}

export const isFinished = (exam) => daysUntil(exam.exam_date) < 0

export function examLabel(days) {
  if (days < 0) return 'Klausur vorbei'
  if (days === 0) return 'Klausur heute'
  if (days === 1) return 'Klausur morgen'
  return `Klausur in ${days} Tagen`
}

function ProgressChart({ history, total }) {
  const [active, setActive] = useState(null)
  const todayUtc = new Date().toISOString().slice(0, 10)
  const last = history.length - 1
  const reached = history.findLastIndex((d) => d.date <= todayUtc)
  const todayIndex = reached < 0 ? 0 : reached
  const progress = history.slice(0, todayIndex + 1)
  const n = progress.length
  const today = progress[n - 1]
  const hasExam = todayIndex < last
  const span = Math.max(hasExam ? last : n - 1, 1)
  const max = Math.max(total, ...progress.map((d) => d.consolidated), 1)
  const x = (i) => (i / span) * 100
  const y = (value) => 100 - (value / max) * 100
  const line = progress.map((d, i) => `${i ? 'L' : 'M'}${x(i)} ${y(d.consolidated)}`).join(' ')
  const todayX = x(n - 1)
  const day = active !== null ? progress[active] : null
  const edge = active !== null && (x(active) < 20 ? 'start' : x(active) > 80 ? 'end' : 'mid')
  const first = history[0].date
  const examDay = history[last].date

  const pick = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const ratio = (e.clientX - box.left) / box.width
    setActive(Math.min(n - 1, Math.max(0, Math.round(ratio * span))))
  }
  const onKey = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(n - 1, Math.max(0, (i ?? n - 1) + step)))
  }

  return (
    <div className="rchart">
      <p className="rchart-head">
        <b>{today.consolidated}</b> von {cardCount(total)} gefestigt
      </p>
      <div
        className="rchart-plot pchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Gefestigte Karten pro Tag seit ${axisFormat.format(localDate(first))}, aktuell ${today.consolidated} von ${total}`}
        onPointerMove={pick}
        onPointerDown={pick}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        <span className="pchart-max">{cardCount(max)}</span>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="pchart-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" style={{ stopColor: 'var(--accent)', stopOpacity: 0.34 }} />
              <stop offset="1" style={{ stopColor: 'var(--accent)', stopOpacity: 0.03 }} />
            </linearGradient>
          </defs>
          <path className="rchart-area" d={`${line} L${todayX} 100 L0 100 Z`} />
          <path className="rchart-line" d={line} vectorEffect="non-scaling-stroke" />
        </svg>
        {hasExam && <i className="pchart-today" style={{ left: `${todayX}%` }} />}
        <i className="rchart-dot" style={{ left: `${x(active ?? n - 1)}%`, top: `${y((day ?? today).consolidated)}%` }} />
        {day && (
          <div className={`tip tip-${edge}`} style={{ left: `${x(active)}%` }}>
            <span className="tip-title">
              {hasExam && active === n - 1 ? 'Heute' : dayFormat.format(localDate(day.date))}
            </span>
            <span className="tip-row"><b>{day.consolidated}</b> von {cardCount(max)} gefestigt</span>
          </div>
        )}
      </div>
      <div className="rchart-axis pchart-axis">
        <span>{axisFormat.format(localDate(first))}</span>
        {hasExam && todayX > 18 && todayX < 78 && (
          <span className="pchart-axis-today" style={{ left: `${todayX}%` }}>Heute</span>
        )}
        <span>Klausur · {axisFormat.format(localDate(examDay))}</span>
      </div>
    </div>
  )
}

export function ProgressFigure({ history, stats }) {
  return (
    <figure className="chart">
      <figcaption>Fortschritt bis zur Klausur</figcaption>
      {history.length > 0 ? (
        <ProgressChart history={history} total={totalCards(stats)} />
      ) : (
        <p className="muted small">Sobald es Karten gibt, siehst du hier, wie viele davon gefestigt sind.</p>
      )}
    </figure>
  )
}

const FORECAST_DAYS = 14

function dueForecast(cards) {
  const today = startOfDay(Date.now())
  const days = Array.from({ length: FORECAST_DAYS }, (_, i) => {
    const date = new Date(today)
    date.setDate(date.getDate() + i)
    return { date, count: 0 }
  })
  for (const card of cards) {
    const index = Math.max(Math.round((startOfDay(card.due) - today) / DAY_MS), 0)
    if (index < FORECAST_DAYS) days[index].count += 1
  }
  return days
}

function ForecastChart({ forecast }) {
  const [active, setActive] = useState(null)
  const n = forecast.length
  const total = forecast.reduce((sum, d) => sum + d.count, 0)
  const max = Math.max(...forecast.map((d) => d.count), 1)
  const day = active !== null ? forecast[active] : null
  const edge = active !== null && (active < n * 0.2 ? 'start' : active > n * 0.8 ? 'end' : 'mid')

  const onKey = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(n - 1, Math.max(0, (i ?? -1) + step)))
  }

  return (
    <div className="rchart">
      <p className="rchart-head">
        <b>{total}</b> {total === 1 ? 'Karte wird' : 'Karten werden'} fällig
        {total > 0 && <span> · davon {forecast[0].count} heute</span>}
      </p>
      <div
        className="rchart-plot fchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Fällige Karten pro Tag, ${total} in den nächsten ${n} Tagen, davon ${forecast[0].count} heute`}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        {forecast.map((d, i) => (
          <div
            key={i}
            className={`fchart-col${i === active ? ' is-active' : ''}`}
            onPointerEnter={() => setActive(i)}
            onPointerDown={() => setActive(i)}
          >
            <i className={i === 0 ? 'is-today' : ''} style={{ height: `${(d.count / max) * 100}%` }} />
          </div>
        ))}
        {day && (
          <div className={`tip tip-${edge}`} style={{ left: `${((active + 0.5) / n) * 100}%` }}>
            <span className="tip-title">{active === 0 ? 'Heute' : dayFormat.format(day.date)}</span>
            <span className="tip-row"><b>{day.count}</b> {cardsLabel(day.count)} fällig</span>
          </div>
        )}
      </div>
      <div className="rchart-axis">
        <span>Heute</span>
        <span>{axisFormat.format(forecast[Math.floor(n / 2)].date)}</span>
        <span>{axisFormat.format(forecast[n - 1].date)}</span>
      </div>
    </div>
  )
}

export function ForecastFigure({ cards }) {
  return (
    <figure className="chart">
      <figcaption>Fälligkeiten · nächste {FORECAST_DAYS} Tage</figcaption>
      <ForecastChart forecast={dueForecast(cards)} />
    </figure>
  )
}

export function StatsPanel({ stats, extraTile, chart, children }) {
  return (
    <section className="panel">
      <div className="tiles">
        <div className="tile">
          <span className="tile-value accent">{stats.due}</span>
          <span className="tile-label">Jetzt fällig</span>
        </div>
        <div className="tile">
          <span className="tile-value">{totalCards(stats)}</span>
          <span className="tile-label">Karten</span>
        </div>
        {extraTile}
      </div>

      <div className="charts">
        <figure className="chart">
          <figcaption>Vorbereitung</figcaption>
          <StatePie stats={stats} />
        </figure>
        {chart}
      </div>

      {children && <div className="row">{children}</div>}
    </section>
  )
}

export function OverviewCard({ to, title, description, stats, meta }) {
  return (
    <Link to={to} className="ocard">
      <div className="ocard-head">
        <h3>{title}</h3>
        {stats.due > 0 && <span className="pill pill-accent">{stats.due} fällig</span>}
      </div>
      {description && <p className="ocard-desc"><RichText text={description} /></p>}
      <div className="ocard-foot">
        <Pie stats={stats} size={44} thickness={7} />
        <div className="ocard-meta">
          <span>{cardCount(totalCards(stats))} · {consolidatedPercent(stats)} % gefestigt</span>
          {meta && <span>{meta}</span>}
        </div>
      </div>
    </Link>
  )
}

export function Loading() {
  return <p className="muted center pad">Lädt …</p>
}

export function LoadError({ error }) {
  return (
    <div className="empty">
      <h3>Das hat nicht geklappt</h3>
      <p className="muted">{error.message}</p>
      <Link to="/" className="btn">Zur Übersicht</Link>
    </div>
  )
}

export function NotFound() {
  return (
    <div className="empty">
      <h3>Seite nicht gefunden</h3>
      <p className="muted">Unter dieser Adresse gibt es nichts.</p>
      <Link to="/" className="btn">Zur Übersicht</Link>
    </div>
  )
}
