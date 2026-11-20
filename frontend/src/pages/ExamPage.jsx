import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadJson, loadExamDecks, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { Breadcrumbs } from '../components/Layout.jsx'
import { ConfirmDialog } from '../components/Modal.jsx'
import { ExamForm, DeckForm, ImportForm } from '../components/Forms.jsx'
import RichText from '../components/RichText.jsx'
import {
  OverviewCard,
  ProgressFigure,
  StatsPanel,
  Loading,
  LoadError,
  byName,
  cardCount,
  daysUntil,
  examLabel,
  formatExamDate,
  totalCards,
} from '../components/Stats.jsx'

export default function ExamPage() {
  const { examId } = useParams()
  const id = Number(examId)
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null)
  const [notice, setNotice] = useState(null)
  const { data, error, loading, reload } = useLoad(
    () => Promise.all([api.exam(id), api.examStats(id), loadExamDecks(id), api.examHistory(id), api.exams()]),
    [id],
  )

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [exam, stats, examDecks, history, exams] = data
  const decks = [...examDecks].sort(byName)
  const days = daysUntil(exam.exam_date)
  const total = totalCards(stats)
  const close = () => setDialog(null)

  const exportExam = async () => {
    try {
      downloadJson(await api.exportExam(id), exam.name)
    } catch (e) {
      setNotice(e.message)
    }
  }

  const onImported = ({ type, created, cards }) => {
    if (type === 'exam') return navigate(`/exams/${created.id}`)
    close()
    setNotice(`„${created.name}“ importiert (${cardCount(cards)}).`)
    reload()
  }

  return (
    <>
      <Breadcrumbs items={[{ label: 'Übersicht', to: '/' }, { label: exam.name }]} />

      <header className="page-head">
        <div>
          <p className="eyebrow">{examLabel(days)}</p>
          <h1>{exam.name}</h1>
          <p className="lead">{formatExamDate(exam.exam_date)}</p>
          {exam.description && <p className="lead"><RichText text={exam.description} /></p>}
        </div>
        <div className="row">
          <button className="icon-btn" data-tip="Klausur bearbeiten" aria-label="Klausur bearbeiten" onClick={() => setDialog('edit')}><Icon name="edit" /></button>
          <button className="icon-btn" data-tip="Klausur exportieren" aria-label="Klausur exportieren" onClick={exportExam}><Icon name="download" /></button>
          <button className="icon-btn" data-tip="Deck importieren" aria-label="Deck importieren" onClick={() => setDialog('import')}><Icon name="upload" /></button>
          <button className="icon-btn danger" data-tip="Klausur löschen" data-tip-align="end" aria-label="Klausur löschen" onClick={() => setDialog('delete')}><Icon name="trash" /></button>
        </div>
      </header>

      {notice && <p className="notice" onClick={() => setNotice(null)}>{notice}</p>}

      <StatsPanel
        stats={stats}
        chart={<ProgressFigure history={history} stats={stats} />}
        extraTile={
          <div className="tile">
            <span className="tile-value">{Math.max(days, 0)}</span>
            <span className="tile-label">{days === 1 ? 'Tag' : 'Tage'} bis zur Klausur</span>
          </div>
        }
      >
        {stats.due > 0 ? (
          <Link to={`/study/exam/${id}`} className="btn btn-primary">Fällige lernen</Link>
        ) : (
          <span className="muted">Nichts fällig.</span>
        )}
        {total > 0 && (
          <Link to={`/study/exam/${id}?mode=all`} className="btn" title="Alle Karten ohne Bewertung durchgehen">Freies Üben</Link>
        )}
      </StatsPanel>

      <section>
        <div className="section-head">
          <h2 className="section-title">Decks</h2>
          <button className="btn btn-small" onClick={() => setDialog('deck')}><Icon name="plus" size={16} /> Deck</button>
        </div>
        {decks.length === 0 ? (
          <div className="empty">
            <p className="muted">Diese Klausur hat noch keine Decks.</p>
            <button className="btn btn-primary" onClick={() => setDialog('deck')}>Erstes Deck anlegen</button>
          </div>
        ) : (
          <div className="grid">
            {decks.map((d) => (
              <OverviewCard key={d.id} to={`/decks/${d.id}`} title={d.name} description={d.description} stats={d.stats} />
            ))}
          </div>
        )}
      </section>

      {dialog === 'edit' && (
        <ExamForm exam={exam} onClose={close} onSaved={() => { close(); reload() }} />
      )}
      {dialog === 'deck' && (
        <DeckForm exams={exams} defaultExamId={id} onClose={close} onSaved={(d) => navigate(`/decks/${d.id}`)} />
      )}
      {dialog === 'import' && (
        <ImportForm exams={exams} defaultExamId={id} onClose={close} onImported={onImported} />
      )}
      {dialog === 'delete' && (
        <ConfirmDialog
          title="Klausur löschen?"
          text={`„${exam.name}“ wird mit ${decks.length} ${decks.length === 1 ? 'Deck' : 'Decks'} und ${cardCount(total)} endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteExam(id)
            navigate('/')
          }}
        />
      )}
    </>
  )
}
