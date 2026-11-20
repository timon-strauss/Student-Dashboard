import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, loadExamsOverview, loadGradesOverview, loadLooseDecks, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { ExamForm, DeckForm, ImportForm } from '../components/Forms.jsx'
import { GradeFigure, GradeTiles } from '../components/Grades.jsx'
import {
  OverviewCard,
  Loading,
  LoadError,
  byName,
  daysUntil,
  examLabel,
  isFinished,
  totalCards,
} from '../components/Stats.jsx'

function GradesSection() {
  const { data, error, loading } = useLoad(loadGradesOverview, [])

  return (
    <section>
      <div className="section-head">
        <h2 className="section-title">Noten</h2>
        <Link to="/grades" className="btn btn-small">Details <Icon name="next" size={16} /></Link>
      </div>
      {error ? (
        <p className="muted small">Noten konnten nicht geladen werden: {error.message}</p>
      ) : loading && !data ? (
        <p className="muted small">Lädt …</p>
      ) : data.progression.length === 0 ? (
        <div className="empty">
          <p className="muted">Noch keine Noten erfasst.</p>
          <Link to="/grades" className="btn btn-primary">Erstes Jahr anlegen</Link>
        </div>
      ) : (
        <div className="panel panel-flush">
          <div className="charts charts-grades">
            <GradeTiles overall={data.overall} />
            <GradeFigure progression={data.progression} />
          </div>
        </div>
      )}
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
      meta={`${exam.deckCount} ${exam.deckCount === 1 ? 'Deck' : 'Decks'} · ${examLabel(days(exam))}`}
    />
  )

  const onImported = ({ type, created }) => navigate(type === 'exam' ? `/exams/${created.id}` : `/decks/${created.id}`)

  return (
    <>
      <GradesSection />

      <section className="hero">
        <p className="eyebrow">Heute</p>
        <h1>
          {total === 0
            ? 'Willkommen. Leg los mit deinem ersten Deck.'
            : due > 0
              ? <>{due} {due === 1 ? 'Karte wartet' : 'Karten warten'} auf dich.</>
              : 'Alles erledigt. Nichts ist fällig.'}
        </h1>
        <div className="row">
          {due > 0 && (
            <Link to="/study/all" className="btn btn-primary btn-large">Jetzt lernen</Link>
          )}
          <button className="btn" onClick={() => setDialog('exam')}><Icon name="plus" /> Klausur</button>
          <button className="btn" onClick={() => setDialog('deck')}><Icon name="plus" /> Deck</button>
          <button className="btn btn-ghost" onClick={() => setDialog('import')}><Icon name="upload" /> Importieren</button>
        </div>
      </section>

      {isEmpty && (
        <div className="empty">
          <h3>Noch nichts hier</h3>
          <p className="muted">
            Eine Klausur bündelt die Decks, die du dafür lernst. Decks können aber auch für sich allein stehen.
          </p>
        </div>
      )}

      {upcoming.length > 0 && (
        <section>
          <h2 className="section-title">Klausuren</h2>
          <div className="grid">{upcoming.map(examCard)}</div>
        </section>
      )}

      {looseDecks.length > 0 && (
        <section>
          <h2 className="section-title">Decks ohne Klausur</h2>
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
            <Icon name="next" size={16} /> Abgeschlossen <span className="pill">{finished.length}</span>
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
