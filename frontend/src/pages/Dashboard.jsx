import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, loadExamsOverview, loadGradesOverview, loadLooseDecks, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { ExamForm, DeckForm, ImportForm } from '../components/Forms.jsx'
import { GradeFigure, formatGrade } from '../components/Grades.jsx'
import { OverviewCard, Loading, LoadError, byName, daysUntil, isFinished, totalCards } from '../components/Stats.jsx'

function GradesStrip() {
  const { data, error } = useLoad(loadGradesOverview, [])
  if (error || !data || data.progression.length === 0) return null
  const { overall, progression } = data

  return (
    <section>
      <div className="section-head">
        <h2 className="section-title">Noten</h2>
        <Link to="/grades" className="btn btn-ghost btn-small">Alle Noten <Icon name="next" size={16} /></Link>
      </div>
      <div className="panel gstrip">
        <div className="gstrip-figures">
          <div className="figure">
            <b className="accent">{formatGrade(overall.grade)}</b>
            <span>Durchschnitt</span>
          </div>
          <div className="figure">
            <b>{overall.passed_ects}</b>
            <span>ECTS</span>
          </div>
          <div className="figure">
            <b>{overall.ects}</b>
            <span>ECTS benotet</span>
          </div>
        </div>
        {progression.length > 1 && <GradeFigure progression={progression} />}
      </div>
    </section>
  )
}

function Today({ due }) {
  if (due === 0) {
    return (
      <section className="today is-done">
        <span className="today-check"><Icon name="check" size={20} /></span>
        <h1>Alles gelernt für heute</h1>
      </section>
    )
  }
  return (
    <section className="today">
      <h1>
        <b>{due}</b> {due === 1 ? 'Karte' : 'Karten'} fällig
      </h1>
      <Link to="/study/all" className="btn btn-primary btn-large">
        Lernen <Icon name="next" />
      </Link>
    </section>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null)
  const { data, error, loading } = useLoad(
    () => Promise.all([loadExamsOverview(), loadLooseDecks(), api.dueCount()]),
    [],
  )

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [exams, decks, { due }] = data
  const looseDecks = [...decks].sort(byName)
  const total = [...exams, ...decks].reduce((sum, item) => sum + totalCards(item.stats), 0)
  const isEmpty = exams.length === 0 && decks.length === 0

  const days = (exam) => daysUntil(exam.exam_date)
  const finished = exams.filter(isFinished).sort((a, b) => days(b) - days(a))
  const upcoming = exams.filter((exam) => !isFinished(exam)).sort((a, b) => days(a) - days(b))

  const examCard = (exam) => (
    <OverviewCard
      key={exam.id}
      to={`/exams/${exam.id}`}
      title={exam.name}
      description={exam.description}
      stats={exam.stats}
      days={days(exam)}
    />
  )

  const onImported = ({ type, created }) => navigate(type === 'exam' ? `/exams/${created.id}` : `/decks/${created.id}`)

  const addButtons = (
    <div className="row">
      <button className="icon-btn" data-tip="Importieren" aria-label="Importieren" onClick={() => setDialog('import')}>
        <Icon name="upload" />
      </button>
      <button className="btn btn-small" onClick={() => setDialog('deck')}><Icon name="plus" size={16} /> Deck</button>
      <button className="btn btn-small" onClick={() => setDialog('exam')}><Icon name="plus" size={16} /> Klausur</button>
    </div>
  )

  return (
    <>
      <GradesStrip />

      {isEmpty ? (
        <section className="empty empty-start">
          <h1>Was steht an?</h1>
          <p className="muted">Leg eine Klausur an und sammle darin deine Decks.</p>
          <div className="row center">
            <button className="btn btn-primary" onClick={() => setDialog('exam')}><Icon name="plus" /> Klausur</button>
            <button className="btn" onClick={() => setDialog('deck')}><Icon name="plus" /> Deck</button>
            <button className="btn btn-ghost" onClick={() => setDialog('import')}><Icon name="upload" /> Importieren</button>
          </div>
        </section>
      ) : (
        total > 0 && <Today due={due} />
      )}

      {!isEmpty && (
        <section>
          <div className="section-head">
            <h2 className="section-title">Klausuren</h2>
            {addButtons}
          </div>
          {upcoming.length > 0 ? (
            <div className="grid">{upcoming.map(examCard)}</div>
          ) : (
            <p className="muted small">Keine anstehenden Klausuren.</p>
          )}
        </section>
      )}

      {looseDecks.length > 0 && (
        <section>
          <h2 className="section-title">Einzelne Decks</h2>
          <div className="grid">
            {looseDecks.map((d) => (
              <OverviewCard key={d.id} to={`/decks/${d.id}`} title={d.name} description={d.description} stats={d.stats} />
            ))}
          </div>
        </section>
      )}

      {finished.length > 0 && (
        <details className="fold">
          <summary>
            <Icon name="next" size={16} /> Vergangene Klausuren <span className="pill">{finished.length}</span>
          </summary>
          <div className="grid">{finished.map(examCard)}</div>
        </details>
      )}

      {dialog === 'exam' && (
        <ExamForm onClose={() => setDialog(null)} onSaved={(exam) => navigate(`/exams/${exam.id}`)} />
      )}
      {dialog === 'deck' && (
        <DeckForm exams={exams} onClose={() => setDialog(null)} onSaved={(d) => navigate(`/decks/${d.id}`)} />
      )}
      {dialog === 'import' && (
        <ImportForm exams={exams} onClose={() => setDialog(null)} onImported={onImported} />
      )}
    </>
  )
}
