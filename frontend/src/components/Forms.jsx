import { useEffect, useRef, useState } from 'react'
import { api, imageUrl } from '../api.js'
import Modal, { useAction } from './Modal.jsx'
import Icon from './Icon.jsx'

function Actions({ busy, onClose, label = 'Speichern', children }) {
  return (
    <div className="modal-actions">
      <button type="button" className="btn" onClick={onClose}>Abbrechen</button>
      {children}
      <button type="submit" className="btn btn-primary" disabled={busy}>{label}</button>
    </div>
  )
}

const pad = (n) => String(n).padStart(2, '0')

function localParts(iso) {
  if (!iso) return { date: '', time: '09:00' }
  const d = new Date(iso)
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
  }
}

export function ExamForm({ exam, onSaved, onClose }) {
  const initial = localParts(exam?.exam_date)
  const [name, setName] = useState(exam?.name ?? '')
  const [description, setDescription] = useState(exam?.description ?? '')
  const [date, setDate] = useState(initial.date)
  const [time, setTime] = useState(initial.time)
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = {
      name: name.trim(),
      description: description.trim() || null,
      exam_date: new Date(`${date}T${time || '09:00'}`).toISOString(),
    }
    run(async () => {
      const saved = exam ? await api.updateExam(exam.id, body) : await api.createExam(body)
      onSaved(saved)
    })
  }

  return (
    <Modal title={exam ? 'Klausur bearbeiten' : 'Neue Klausur'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Analysis I" />
        </label>
        <label className="field">
          <span>Beschreibung <em>optional</em></span>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Klausurtermin</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>
          <label className="field">
            <span>Uhrzeit</span>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !name.trim() || !date} onClose={onClose} />
      </form>
    </Modal>
  )
}

function ExamSelect({ exams, value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Keine Klausur</option>
      {exams.map((exam) => (
        <option key={exam.id} value={exam.id}>{exam.name}</option>
      ))}
    </select>
  )
}

export function DeckForm({ deck, exams, defaultExamId = null, onSaved, onClose }) {
  const [name, setName] = useState(deck?.name ?? '')
  const [description, setDescription] = useState(deck?.description ?? '')
  const [examId, setExamId] = useState(String(deck ? deck.exam_id ?? '' : defaultExamId ?? ''))
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = {
      name: name.trim(),
      description: description.trim() || null,
      exam_id: examId ? Number(examId) : null,
    }
    run(async () => {
      const saved = deck ? await api.updateDeck(deck.id, body) : await api.createDeck(body)
      onSaved(saved)
    })
  }

  return (
    <Modal title={deck ? 'Deck bearbeiten' : 'Neues Deck'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Grenzwerte" />
        </label>
        <label className="field">
          <span>Beschreibung <em>optional</em></span>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label className="field">
          <span>Klausur</span>
          <ExamSelect exams={exams} value={examId} onChange={setExamId} />
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !name.trim()} onClose={onClose} />
      </form>
    </Modal>
  )
}

function Dropzone({ accept, matches, onFile, rejectText, className = '', children }) {
  const input = useRef(null)
  const [over, setOver] = useState(false)
  const [rejected, setRejected] = useState(false)

  const take = (file) => {
    if (!file) return
    const ok = matches(file)
    setRejected(!ok)
    if (ok) onFile(file)
  }

  return (
    <>
      <div
        className={`dropzone ${over ? 'is-over' : ''} ${className}`}
        role="button"
        tabIndex={0}
        onClick={() => input.current.click()}
        onKeyDown={(e) => {
          if (e.target !== e.currentTarget) return
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) return
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            input.current.click()
          }
        }}
        onDragOver={(e) => {
          e.preventDefault()
          e.dataTransfer.dropEffect = 'copy'
          setOver(true)
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget)) setOver(false)
        }}
        onDrop={(e) => {
          e.preventDefault()
          setOver(false)
          take(e.dataTransfer.files[0])
        }}
      >
        <input
          ref={input}
          type="file"
          accept={accept}
          hidden
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            const file = e.target.files[0]
            e.target.value = ''
            take(file)
          }}
        />
        {children}
      </div>
      {rejected && <p className="error dropzone-error">{rejectText}</p>}
    </>
  )
}

const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/avif']
const isImage = (file) => IMAGE_TYPES.includes(file.type)

const emptyImage = (existing) => ({ existing: existing ?? null, file: null, preview: null })

function ImageField({ value, onChange }) {
  const src = value.preview ?? imageUrl(value.existing)

  useEffect(() => () => value.preview && URL.revokeObjectURL(value.preview), [value.preview])

  return (
    <div className="image-field">
      <Dropzone
        accept={IMAGE_TYPES.join(',')}
        matches={isImage}
        rejectText="Nur PNG, JPEG, GIF, WebP oder AVIF."
        className={src ? 'has-file' : ''}
        onFile={(file) => onChange({ existing: null, file, preview: URL.createObjectURL(file) })}
      >
        {src ? (
          <>
            <img src={src} alt="" />
            <span className="dropzone-text">Klicken oder Bild hierher ziehen, um es zu ersetzen</span>
            <button
              type="button"
              className="dropzone-remove"
              title="Bild entfernen"
              aria-label="Bild entfernen"
              onClick={(e) => {
                e.stopPropagation()
                onChange(emptyImage())
              }}
            >
              <Icon name="close" size={16} />
            </button>
          </>
        ) : (
          <>
            <Icon name="image" size={20} />
            <span className="dropzone-text">Bild hierher ziehen oder klicken</span>
          </>
        )}
      </Dropzone>
    </div>
  )
}

const storedImage = async (image) => (image.file ? api.uploadImage(image.file) : image.existing)

export function CardForm({ card, deckId, onSaved, onClose }) {
  const [front, setFront] = useState(card?.front ?? '')
  const [back, setBack] = useState(card?.back ?? '')
  const [frontImage, setFrontImage] = useState(() => emptyImage(card?.front_image))
  const [backImage, setBackImage] = useState(() => emptyImage(card?.back_image))
  const [added, setAdded] = useState(0)
  const { busy, error, run } = useAction()
  const frontRef = useRef(null)

  const save = (keepOpen) =>
    run(async () => {
      const [frontName, backName] = await Promise.all([storedImage(frontImage), storedImage(backImage)])
      const body = { front: front.trim(), back: back.trim(), front_image: frontName, back_image: backName }
      if (card) {
        await api.updateCard(card.id, body)
      } else {
        await api.createCard({ deck_id: deckId, ...body })
      }
      if (keepOpen) {
        setFront('')
        setBack('')
        setFrontImage(emptyImage())
        setBackImage(emptyImage())
        setAdded((n) => n + 1)
        frontRef.current?.focus()
        onSaved(true)
      } else {
        onSaved(false)
      }
    })

  const valid = front.trim() && back.trim()

  return (
    <Modal title={card ? 'Karte bearbeiten' : 'Neue Karte'} onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (valid) save(false)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && valid && !busy) {
            e.preventDefault()
            save(!card)
          }
        }}
      >
        <div className="card-form">
          <div>
            <label className="field">
              <span>Frage</span>
              <textarea ref={frontRef} rows={5} value={front} onChange={(e) => setFront(e.target.value)} required autoFocus />
            </label>
            <ImageField value={frontImage} onChange={setFrontImage} />
          </div>
          <div>
            <label className="field">
              <span>Antwort</span>
              <textarea rows={5} value={back} onChange={(e) => setBack(e.target.value)} required />
            </label>
            <ImageField value={backImage} onChange={setBackImage} />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {added > 0 && !error && (
          <p className="muted small">{added} {added === 1 ? 'Karte' : 'Karten'} hinzugefügt.</p>
        )}
        <Actions busy={busy || !valid} onClose={onClose}>
          {!card && (
            <button type="button" className="btn" disabled={busy || !valid} onClick={() => save(true)} title="⌘/Strg + Enter">
              Speichern &amp; nächste
            </button>
          )}
        </Actions>
      </form>
    </Modal>
  )
}

const isJson = (file) => file.type === 'application/json' || file.name.toLowerCase().endsWith('.json')

async function readTransfer(file) {
  let data
  try {
    data = JSON.parse(await file.text())
  } catch {
    throw new Error('Die Datei enthält kein gültiges JSON.')
  }
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    if ('exam_date' in data || Array.isArray(data.decks)) return { type: 'exam', data }
    if (typeof data.name === 'string') return { type: 'deck', data }
  }
  throw new Error('Die Datei ist kein Klausur- oder Deck-Export.')
}

export function ImportForm({ exams, defaultExamId = null, onImported, onClose }) {
  const [file, setFile] = useState(null)
  const [examId, setExamId] = useState(String(defaultExamId ?? ''))
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    run(async () => {
      const { type, data } = await readTransfer(file)
      const created =
        type === 'exam' ? await api.importExam(data) : await api.importDeck(data, examId ? Number(examId) : null)
      onImported({ type, created, cards: type === 'deck' ? data.cards?.length ?? 0 : null })
    })
  }

  return (
    <Modal title="Importieren" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="muted">
          Wähle eine zuvor exportierte JSON-Datei. Klausur-Exporte legen eine neue Klausur mit allen Decks an,
          Deck-Exporte ein einzelnes Deck.
        </p>
        <div className="field">
          <span>Datei</span>
          <Dropzone
            accept=".json,application/json"
            matches={isJson}
            rejectText="Nur JSON-Dateien."
            className={`dropzone-large ${file ? 'has-file' : ''}`}
            onFile={setFile}
          >
            <Icon name="upload" size={22} />
            {file ? (
              <span className="dropzone-text">
                <strong>{file.name}</strong>
                <br />
                Klicken oder andere Datei hierher ziehen, um sie zu ersetzen
              </span>
            ) : (
              <span className="dropzone-text">JSON-Datei hierher ziehen oder klicken</span>
            )}
          </Dropzone>
        </div>
        <label className="field">
          <span>Deck einer Klausur zuordnen <em>nur für Deck-Exporte</em></span>
          <ExamSelect exams={exams} value={examId} onChange={setExamId} />
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !file} onClose={onClose} label="Importieren" />
      </form>
    </Modal>
  )
}
