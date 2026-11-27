import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadJson, imageUrl, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { Breadcrumbs, Menu, Notice } from '../components/Layout.jsx'
import { ConfirmDialog } from '../components/Modal.jsx'
import { DeckForm, CardForm } from '../components/Forms.jsx'
import RichText from '../components/RichText.jsx'
import { ForecastFigure, StatsPanel, Loading, LoadError, cardCount, totalCards } from '../components/Stats.jsx'

function dueInfo(card) {
  if (!card.last_review) return { label: 'Neu', tone: 'new' }
  const minutes = Math.round((new Date(card.due) - Date.now()) / 60000)
  if (minutes <= 0) return { label: 'Fällig', tone: 'due' }
  if (minutes < 60) return { label: `in ${minutes} Min.`, tone: 'later' }
  if (minutes < 60 * 24) return { label: `in ${Math.round(minutes / 60)} Std.`, tone: 'later' }
  const days = Math.round(minutes / (60 * 24))
  return { label: days === 1 ? 'morgen' : `in ${days} Tagen`, tone: 'later' }
}

function CardRow({ card, onEdit, onDelete, drag }) {
  const due = dueInfo(card)
  return (
    <li
      className={`crow${drag.activeId === card.id ? ' dragging' : ''}`}
      draggable
      onDragStart={(e) => drag.start(e, card.id)}
      onDragOver={(e) => drag.over(e, card.id)}
      onDragEnd={drag.end}
    >
      <span className="grip" aria-hidden="true"><Icon name="grip" size={16} /></span>
      <div className="crow-side">
        {card.front_image && <img src={imageUrl(card.front_image)} alt="" loading="lazy" />}
        <p><RichText text={card.front} /></p>
      </div>
      <div className="crow-side crow-back">
        {card.back_image && <img src={imageUrl(card.back_image)} alt="" loading="lazy" />}
        <p><RichText text={card.back} /></p>
      </div>
      <span className={`pill pill-${due.tone}`}>{due.label}</span>
      <div className="crow-actions">
        <button className="icon-btn" aria-label="Karte bearbeiten" title="Bearbeiten" onClick={() => onEdit(card)}><Icon name="edit" size={16} /></button>
        <button className="icon-btn danger" aria-label="Karte löschen" title="Löschen" onClick={() => onDelete(card)}><Icon name="trash" size={16} /></button>
      </div>
    </li>
  )
}

export default function DeckPage() {
  const { deckId } = useParams()
  const id = Number(deckId)
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null)
  const [notice, setNotice] = useState(null)
  const { data, error, loading, reload } = useLoad(
    () => Promise.all([api.deck(id), api.deckCards(id), api.deckStats(id), api.exams()]),
    [id],
  )

  const [cards, setCards] = useState([])
  const [activeId, setActiveId] = useState(null)
  const orderBeforeDrag = useRef(null)
  useEffect(() => {
    if (data) setCards(data[1])
  }, [data])

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [deck, , stats, exams] = data
  const exam = exams.find((e) => e.id === deck.exam_id)
  const total = totalCards(stats)
  const close = () => setDialog(null)

  const drag = {
    activeId,
    start: (e, cardId) => {
      e.dataTransfer.effectAllowed = 'move'
      orderBeforeDrag.current = cards
      setActiveId(cardId)
    },
    over: (e, overId) => {
      if (activeId === null) return
      e.preventDefault()
      if (overId === activeId) return
      setCards((list) => {
        const from = list.findIndex((c) => c.id === activeId)
        const to = list.findIndex((c) => c.id === overId)
        const next = [...list]
        next.splice(to, 0, next.splice(from, 1)[0])
        return next
      })
    },
    end: async () => {
      const movedId = activeId
      const before = orderBeforeDrag.current
      setActiveId(null)
      if (movedId === null || !before || before.every((c, i) => c.id === cards[i]?.id)) return
      try {
        await api.repositionCard(movedId, cards.findIndex((c) => c.id === movedId))
      } catch (e) {
        setCards(before)
        setNotice(e.message)
      }
    },
  }

  const exportDeck = async () => {
    try {
      downloadJson(await api.exportDeck(id), deck.name)
    } catch (e) {
      setNotice(e.message)
    }
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Lernen', to: '/' },
          ...(exam ? [{ label: exam.name, to: `/exams/${exam.id}` }] : []),
          { label: deck.name },
        ]}
      />

      <header className="page-head">
        <div className="page-title">
          <h1>{deck.name}</h1>
          {deck.description && <p className="lead"><RichText text={deck.description} /></p>}
        </div>
        <div className="page-actions">
          {total > 0 && (
            <Link to={`/study/deck/${id}?mode=all`} className="btn" data-tip="Ohne Bewertung durchgehen">Üben</Link>
          )}
          {stats.due > 0 && (
            <Link to={`/study/deck/${id}`} className="btn btn-primary">Lernen <span className="btn-count">{stats.due}</span></Link>
          )}
          <Menu
            items={[
              { label: 'Bearbeiten', icon: 'edit', onClick: () => setDialog({ type: 'edit' }) },
              { label: 'Exportieren', icon: 'download', onClick: exportDeck },
              { label: 'Löschen', icon: 'trash', danger: true, onClick: () => setDialog({ type: 'delete' }) },
            ]}
          />
        </div>
      </header>

      <Notice text={notice} onClose={() => setNotice(null)} />

      {total > 0 && <StatsPanel stats={stats} chart={<ForecastFigure cards={cards} />} />}

      <section>
        <div className="section-head">
          <h2 className="section-title">Karten <span className="count">{cards.length}</span></h2>
          {cards.length > 0 && (
            <button className="btn btn-small" onClick={() => setDialog({ type: 'card' })}><Icon name="plus" size={16} /> Karte</button>
          )}
        </div>
        {cards.length === 0 ? (
          <div className="empty">
            <button className="btn btn-primary" onClick={() => setDialog({ type: 'card' })}><Icon name="plus" /> Erste Karte</button>
          </div>
        ) : (
          <ul className="clist">
            {cards.map((c) => (
              <CardRow
                key={c.id}
                card={c}
                drag={drag}
                onEdit={(card) => setDialog({ type: 'card', card })}
                onDelete={(card) => setDialog({ type: 'deleteCard', card })}
              />
            ))}
          </ul>
        )}
      </section>

      {dialog?.type === 'edit' && (
        <DeckForm deck={deck} exams={exams} onClose={close} onSaved={() => { close(); reload() }} />
      )}
      {dialog?.type === 'card' && (
        <CardForm
          card={dialog.card}
          deckId={id}
          onClose={close}
          onSaved={(keepOpen) => {
            if (!keepOpen) close()
            reload()
          }}
        />
      )}
      {dialog?.type === 'deleteCard' && (
        <ConfirmDialog
          title="Karte löschen?"
          text={`„${dialog.card.front.slice(0, 80)}${dialog.card.front.length > 80 ? '…' : ''}“ wird endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteCard(dialog.card.id)
            close()
            reload()
          }}
        />
      )}
      {dialog?.type === 'delete' && (
        <ConfirmDialog
          title="Deck löschen?"
          text={`„${deck.name}“ wird mit ${cardCount(total)} endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteDeck(id)
            navigate(exam ? `/exams/${exam.id}` : '/')
          }}
        />
      )}
    </>
  )
}
