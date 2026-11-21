import { useState } from 'react'
import { gradesApi } from '../api.js'
import Modal, { useAction } from './Modal.jsx'

const PASSING_GRADE = 4.0
const BEST_GRADE = 1.0

const gradeFormat = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
const pointsFormat = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 })

export const formatGrade = (grade) => (grade === null || grade === undefined ? '–' : gradeFormat.format(grade))
export const formatPoints = (points) => pointsFormat.format(points)
export const isFailing = (grade) => grade !== null && grade > PASSING_GRADE
export const ectsLabel = (ects) => `${ects} ECTS`

function GradeChart({ progression }) {
  const [active, setActive] = useState(null)
  const n = progression.length
  const shown = progression.flatMap((p) => [p.grade, p.cumulative_grade]).filter((g) => g !== null)
  const top = Math.max(BEST_GRADE, Math.floor((Math.min(...shown) - 0.1) * 2) / 2)
  const bottom = Math.min(PASSING_GRADE, Math.max(Math.ceil((Math.max(...shown) + 0.1) * 2) / 2, top + 0.5))
  const x = (i) => (n === 1 ? 50 : 4 + (i / (n - 1)) * 92)
  const y = (grade) => ((Math.min(Math.max(grade, top), bottom) - top) / (bottom - top)) * 100
  const points = progression
    .map((p, i) => ({ i, grade: p.cumulative_grade }))
    .filter((p) => p.grade !== null)
  const line = points.map((p, k) => `${k ? 'L' : 'M'}${x(p.i)} ${y(p.grade)}`).join(' ')
  const current = points.length ? points[points.length - 1].grade : null
  const entry = active !== null ? progression[active] : null
  const edge = active !== null && (x(active) < 20 ? 'start' : x(active) > 80 ? 'end' : 'mid')

  const pick = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const ratio = ((e.clientX - box.left) / box.width) * 100
    let best = 0
    progression.forEach((_, i) => {
      if (Math.abs(x(i) - ratio) < Math.abs(x(best) - ratio)) best = i
    })
    setActive(best)
  }
  const onKey = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(n - 1, Math.max(0, (i ?? n - 1) + step)))
  }

  return (
    <div className="rchart">
      <div
        className="rchart-plot gchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Notenverlauf über ${n} ${n === 1 ? 'Jahr' : 'Jahre'}, aktueller Durchschnitt ${formatGrade(current)}`}
        onPointerMove={pick}
        onPointerDown={pick}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        <span className="gchart-label gchart-label-top">{formatGrade(top)}</span>
        <span className="gchart-label gchart-label-bottom">{formatGrade(bottom)}</span>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {points.length > 1 && <path className="rchart-line" d={line} vectorEffect="non-scaling-stroke" />}
        </svg>
        {progression.map((p, i) =>
          p.grade !== null ? (
            <i
              key={`year-${p.year_id}`}
              className={`gchart-year${i === active ? ' is-active' : ''}`}
              style={{ left: `${x(i)}%`, top: `${y(p.grade)}%` }}
            />
          ) : null,
        )}
        {points.map((p) => (
          <i
            key={`avg-${p.i}`}
            className={`rchart-dot${p.i === active ? ' is-active' : ''}`}
            style={{ left: `${x(p.i)}%`, top: `${y(p.grade)}%` }}
          />
        ))}
        {entry && (
          <div className={`tip tip-${edge}`} style={{ left: `${x(active)}%` }}>
            <span className="tip-title">{entry.year}</span>
            <span className="tip-row">
              Jahr <b>{formatGrade(entry.grade)}</b>
            </span>
            <span className="tip-row">
              Gesamt <b>{formatGrade(entry.cumulative_grade)}</b>
            </span>
          </div>
        )}
      </div>
      <div className="gchart-axis">
        {progression.map((p, i) => (
          <span key={p.year_id} style={{ left: `${x(i)}%` }}>{p.year}</span>
        ))}
      </div>
      <ul className="gchart-legend">
        <li><i className="gchart-key-avg" /> Gesamtdurchschnitt</li>
        <li><i className="gchart-key-year" /> Jahresschnitt</li>
      </ul>
    </div>
  )
}

export function GradeFigure({ progression }) {
  const hasGrades = progression.some((p) => p.cumulative_grade !== null)
  return (
    <figure className="chart">
      <figcaption>Notenverlauf</figcaption>
      {hasGrades ? (
        <GradeChart progression={progression} />
      ) : (
        <p className="muted small">Noch keine Noten.</p>
      )}
    </figure>
  )
}

function Actions({ busy, onClose }) {
  return (
    <div className="modal-actions">
      <button type="button" className="btn" onClick={onClose}>Abbrechen</button>
      <button type="submit" className="btn btn-primary" disabled={busy}>Speichern</button>
    </div>
  )
}

const toNumber = (value) => (value === '' ? null : Number(value))

export function YearForm({ year, onSaved, onClose }) {
  const [label, setLabel] = useState(year?.year ?? '')
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = { year: label.trim() }
    run(async () => {
      onSaved(year ? await gradesApi.updateYear(year.id, body) : await gradesApi.createYear(body))
    })
  }

  return (
    <Modal title={year ? 'Jahr bearbeiten' : 'Neues Jahr'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={label} onChange={(e) => setLabel(e.target.value)} required autoFocus placeholder="z. B. 2025/26" />
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !label.trim()} onClose={onClose} />
      </form>
    </Modal>
  )
}

export function ModuleForm({ module, years, yearId, onSaved, onClose }) {
  const fromSubmodules = module?.grade_from_submodules ?? false
  const [name, setName] = useState(module?.name ?? '')
  const [ects, setEcts] = useState(module ? String(module.ects) : '')
  const [targetYear, setTargetYear] = useState(String(module?.year_id ?? yearId))
  const [grade, setGrade] = useState(module && !fromSubmodules && module.grade !== null ? String(module.grade) : '')
  const [passed, setPassed] = useState(module && !fromSubmodules && module.grade === null ? module.passed : false)
  const { busy, error, run } = useAction()
  const hasGrade = grade !== ''

  const submit = (e) => {
    e.preventDefault()
    const body = { name: name.trim(), ects: Number(ects), year_id: Number(targetYear) }
    if (!fromSubmodules) {
      body.grade = toNumber(grade)
      body.passed = hasGrade ? false : passed
    }
    run(async () => {
      onSaved(module ? await gradesApi.updateModule(module.id, body) : await gradesApi.createModule(body))
    })
  }

  return (
    <Modal title={module ? 'Modul bearbeiten' : 'Neues Modul'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Analysis I" />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Jahr</span>
            <select value={targetYear} onChange={(e) => setTargetYear(e.target.value)}>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.year}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>ECTS</span>
            <input type="number" min="1" step="1" value={ects} onChange={(e) => setEcts(e.target.value)} required />
          </label>
        </div>
        {fromSubmodules ? (
          <p className="field-hint">Note aus Teilleistungen</p>
        ) : (
          <>
            <label className="field">
              <span>Note <em>optional</em></span>
              <input
                type="number"
                min="1"
                max="6"
                step="0.1"
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                placeholder="1,0 – 6,0"
              />
            </label>
            <label className={`check${hasGrade ? ' is-disabled' : ''}`}>
              <input
                type="checkbox"
                checked={!hasGrade && passed}
                disabled={hasGrade}
                onChange={(e) => setPassed(e.target.checked)}
              />
              <span>Unbenotet bestanden</span>
            </label>
          </>
        )}
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !name.trim() || !ects} onClose={onClose} />
      </form>
    </Modal>
  )
}

export function SubmoduleForm({ submodule, moduleId, maxPoints, onSaved, onClose }) {
  const [name, setName] = useState(submodule?.name ?? '')
  const [max, setMax] = useState(submodule ? String(submodule.max_points) : '')
  const [reached, setReached] = useState(submodule?.reached_points != null ? String(submodule.reached_points) : '')
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = {
      name: name.trim(),
      max_points: Number(max),
      reached_points: toNumber(reached),
    }
    run(async () => {
      onSaved(
        submodule
          ? await gradesApi.updateSubmodule(submodule.id, body)
          : await gradesApi.createSubmodule({ ...body, module_id: moduleId }),
      )
    })
  }

  return (
    <Modal title={submodule ? 'Teilleistung bearbeiten' : 'Neue Teilleistung'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Klausur" />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Erreicht <em>optional</em></span>
            <input
              type="number"
              min="0"
              max={max || undefined}
              step="0.5"
              value={reached}
              onChange={(e) => setReached(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Maximal</span>
            <input
              type="number"
              min="0.5"
              step="0.5"
              list="grade-tables"
              value={max}
              onChange={(e) => setMax(e.target.value)}
              required
            />
            <datalist id="grade-tables">
              {maxPoints.map((p) => (
                <option key={p} value={p} />
              ))}
            </datalist>
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !name.trim() || !max} onClose={onClose} />
      </form>
    </Modal>
  )
}
