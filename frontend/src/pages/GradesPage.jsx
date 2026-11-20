import { useState } from 'react'
import { gradesApi, loadGradesTree, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { Breadcrumbs } from '../components/Layout.jsx'
import { ConfirmDialog } from '../components/Modal.jsx'
import {
  ModuleForm,
  SubmoduleForm,
  YearForm,
  ectsLabel,
  formatGrade,
  formatPoints,
  isFailing,
} from '../components/Grades.jsx'
import { Loading, LoadError } from '../components/Stats.jsx'

const LEVELS = ['year', 'module', 'submodule']

function Grade({ value, level, passedWithoutGrade }) {
  if (value === null && passedWithoutGrade) {
    return <span className={`tgrade tgrade-${level} tgrade-pass`}>bestanden</span>
  }
  return (
    <span className={`tgrade tgrade-${level}${isFailing(value) ? ' tgrade-fail' : ''}${value === null ? ' tgrade-none' : ''}`}>
      {formatGrade(value)}
    </span>
  )
}

function ActionButton({ icon, label, onClick, danger = false, align, disabled = false }) {
  return (
    <button
      className={`icon-btn icon-btn-small${danger ? ' danger' : ''}`}
      data-tip={label}
      data-tip-align={align}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
    >
      <Icon name={icon} size={16} />
    </button>
  )
}

function Row({ level, open, onToggle, title, meta, actions, grade }) {
  const foldable = onToggle !== undefined
  return (
    <div className={`trow trow-${level}`} style={{ '--depth': LEVELS.indexOf(level) }}>
      <div className="trow-main">
        {foldable ? (
          <button className="trow-toggle" aria-expanded={open} onClick={onToggle}>
            <Icon name="next" size={16} />
            <span className="trow-title">{title}</span>
          </button>
        ) : (
          <span className="trow-leaf">
            <i />
            <span className="trow-title">{title}</span>
          </span>
        )}
        {meta && <span className="trow-meta">{meta}</span>}
      </div>
      <div className="trow-actions">{actions}</div>
      {grade}
    </div>
  )
}

const canHaveSubmodules = (module) =>
  module.grade_from_submodules || (module.grade === null && !module.passed)

export default function GradesPage() {
  const [dialog, setDialog] = useState(null)
  const [open, setOpen] = useState(() => new Set())
  const [closedYears, setClosedYears] = useState(() => new Set())
  const [notice, setNotice] = useState(null)
  const { data, error, loading, reload } = useLoad(loadGradesTree, [])

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const { tree, overall, maxPoints } = data
  const close = () => setDialog(null)
  const saved = () => {
    close()
    reload()
  }
  const toggle = (setter, key) =>
    setter((current) => {
      const next = new Set(current)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  const move = async (year, position) => {
    try {
      await gradesApi.repositionYear(year.id, position)
      reload()
    } catch (e) {
      setNotice(e.message)
    }
  }
  const allModulesOpen = tree.every((y) => y.modules.every((m) => m.submodules.length === 0 || open.has(m.id)))
  const toggleAll = () => {
    setClosedYears(new Set())
    setOpen(allModulesOpen ? new Set() : new Set(tree.flatMap((y) => y.modules.map((m) => m.id))))
  }

  return (
    <>
      <Breadcrumbs items={[{ label: 'Übersicht', to: '/' }, { label: 'Noten' }]} />

      <header className="page-head">
        <div>
          <p className="eyebrow">Noten</p>
          <h1>Notenübersicht</h1>
          <p className="lead">
            Durchschnitt {formatGrade(overall.grade)} · {ectsLabel(overall.ects)} benotet
          </p>
        </div>
        <div className="row">
          {tree.length > 0 && (
            <button className="btn btn-ghost" onClick={toggleAll}>
              {allModulesOpen ? 'Alle einklappen' : 'Alle ausklappen'}
            </button>
          )}
          <button className="btn" onClick={() => setDialog({ type: 'year' })}>
            <Icon name="plus" /> Jahr
          </button>
        </div>
      </header>

      {notice && <p className="notice" onClick={() => setNotice(null)}>{notice}</p>}

      {tree.length === 0 ? (
        <div className="empty">
          <h3>Noch keine Jahre</h3>
          <p className="muted">
            Ein Jahr fasst zwei Semester zusammen. Darin legst du Module an, die du direkt benotest oder über Teilleistungen berechnen lässt.
          </p>
          <button className="btn btn-primary" onClick={() => setDialog({ type: 'year' })}>Erstes Jahr anlegen</button>
        </div>
      ) : (
        <section className="tree" aria-label="Jahre, Module und Teilleistungen">
          <div className="tree-head">
            <span>Jahr · Modul · Teilleistung</span>
            <span>Note</span>
          </div>
          {tree.map((year, index) => {
            const yearOpen = !closedYears.has(year.id)
            return (
              <div key={year.id} className="tnode" role="group">
                <Row
                  level="year"
                  open={yearOpen}
                  onToggle={() => toggle(setClosedYears, year.id)}
                  title={year.year}
                  meta={`${year.modules.length} ${year.modules.length === 1 ? 'Modul' : 'Module'} · ${ectsLabel(year.ects)} benotet`}
                  grade={<Grade value={year.grade} level="year" />}
                  actions={
                    <>
                      <ActionButton icon="up" label="Nach oben" disabled={index === 0} onClick={() => move(year, index - 1)} />
                      <ActionButton icon="down" label="Nach unten" disabled={index === tree.length - 1} onClick={() => move(year, index + 1)} />
                      <ActionButton icon="plus" label="Modul anlegen" onClick={() => setDialog({ type: 'module', yearId: year.id })} />
                      <ActionButton icon="edit" label="Bearbeiten" onClick={() => setDialog({ type: 'year', year })} />
                      <ActionButton icon="trash" label="Löschen" danger align="end" onClick={() => setDialog({ type: 'delete-year', year })} />
                    </>
                  }
                />
                {yearOpen && year.modules.length === 0 && (
                  <p className="tree-empty" style={{ '--depth': 1 }}>Noch keine Module.</p>
                )}
                {yearOpen &&
                  year.modules.map((module) => {
                    const moduleOpen = open.has(module.id)
                    const hasSubmodules = module.submodules.length > 0
                    return (
                      <div key={module.id} className="tnode" role="group">
                        <Row
                          level="module"
                          open={moduleOpen}
                          onToggle={hasSubmodules ? () => toggle(setOpen, module.id) : undefined}
                          title={module.name}
                          meta={
                            <>
                              {ectsLabel(module.ects)}
                              {hasSubmodules && ` · ${module.submodules.length} ${module.submodules.length === 1 ? 'Teilleistung' : 'Teilleistungen'}`}
                              {module.grade_from_submodules && module.grade === null && ' · Punkte fehlen noch'}
                            </>
                          }
                          grade={<Grade value={module.grade} level="module" passedWithoutGrade={module.passed} />}
                          actions={
                            <>
                              {canHaveSubmodules(module) && (
                                <ActionButton
                                  icon="plus"
                                  label="Teilleistung anlegen"
                                  onClick={() => setDialog({ type: 'submodule', moduleId: module.id })}
                                />
                              )}
                              <ActionButton icon="edit" label="Bearbeiten" onClick={() => setDialog({ type: 'module', module })} />
                              <ActionButton icon="trash" label="Löschen" danger align="end" onClick={() => setDialog({ type: 'delete-module', module })} />
                            </>
                          }
                        />
                        {moduleOpen &&
                          module.submodules.map((submodule) => (
                            <Row
                              key={submodule.id}
                              level="submodule"
                              title={submodule.name}
                              meta={`${submodule.reached_points === null ? '–' : formatPoints(submodule.reached_points)} / ${formatPoints(submodule.max_points)} Punkte · Gewichtung ${formatPoints(submodule.weight)}`}
                              grade={<Grade value={submodule.grade} level="submodule" />}
                              actions={
                                <>
                                  <ActionButton
                                    icon="edit"
                                    label="Bearbeiten"
                                    onClick={() => setDialog({ type: 'submodule', submodule, moduleId: module.id })}
                                  />
                                  <ActionButton
                                    icon="trash"
                                    label="Löschen"
                                    danger
                                    align="end"
                                    onClick={() => setDialog({ type: 'delete-submodule', submodule })}
                                  />
                                </>
                              }
                            />
                          ))}
                      </div>
                    )
                  })}
              </div>
            )
          })}
        </section>
      )}

      {dialog?.type === 'year' && <YearForm year={dialog.year} onClose={close} onSaved={saved} />}
      {dialog?.type === 'module' && (
        <ModuleForm module={dialog.module} years={tree} yearId={dialog.yearId} onClose={close} onSaved={saved} />
      )}
      {dialog?.type === 'submodule' && (
        <SubmoduleForm
          submodule={dialog.submodule}
          moduleId={dialog.moduleId}
          maxPoints={maxPoints}
          onClose={close}
          onSaved={() => {
            setOpen((current) => new Set(current).add(dialog.moduleId))
            saved()
          }}
        />
      )}
      {dialog?.type === 'delete-year' && (
        <ConfirmDialog
          title="Jahr löschen?"
          text={`„${dialog.year.year}“ wird mit ${dialog.year.modules.length} ${dialog.year.modules.length === 1 ? 'Modul' : 'Modulen'} und allen Teilleistungen endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await gradesApi.deleteYear(dialog.year.id)
            saved()
          }}
        />
      )}
      {dialog?.type === 'delete-module' && (
        <ConfirmDialog
          title="Modul löschen?"
          text={`„${dialog.module.name}“ wird mit allen Teilleistungen endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await gradesApi.deleteModule(dialog.module.id)
            saved()
          }}
        />
      )}
      {dialog?.type === 'delete-submodule' && (
        <ConfirmDialog
          title="Teilleistung löschen?"
          text={`„${dialog.submodule.name}“ wird endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await gradesApi.deleteSubmodule(dialog.submodule.id)
            saved()
          }}
        />
      )}
    </>
  )
}
