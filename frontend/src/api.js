import { useCallback, useEffect, useState } from 'react'

const BASE = '/api'
const GRADES_BASE = '/grades-api'

function errorMessage(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return `Ungültige Eingabe: ${detail[0].msg}`
  return `Anfrage fehlgeschlagen (${status})`
}

async function send(url, options) {
  let res
  try {
    res = await fetch(url, options)
  } catch {
    throw new Error('Server nicht erreichbar. Läuft das Backend?')
  }
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail
    } catch {
      detail = undefined
    }
    throw new Error(errorMessage(detail, res.status))
  }
  return res.status === 204 ? null : res.json()
}

const request = (path, options) => send(BASE + path, options)
const gradesRequest = (path, options) => send(GRADES_BASE + path, options)

const json = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

const cardQuery = (scope, due) => `/cards?${new URLSearchParams({ ...scope, ...(due ? { due: 'true' } : {}) })}`

export const api = {
  exams: () => request('/exams'),
  exam: (id) => request(`/exams/${id}`),
  createExam: (body) => request('/exams', json('POST', body)),
  updateExam: (id, body) => request(`/exams/${id}`, json('PATCH', body)),
  deleteExam: (id) => request(`/exams/${id}`, { method: 'DELETE' }),

  examDecks: (examId) => request(`/decks?exam_id=${examId}`),
  looseDecks: () => request('/decks'),
  deck: (id) => request(`/decks/${id}`),
  createDeck: (body) => request('/decks', json('POST', body)),
  updateDeck: (id, body) => request(`/decks/${id}`, json('PATCH', body)),
  deleteDeck: (id) => request(`/decks/${id}`, { method: 'DELETE' }),

  deckCards: (deckId, due = false) => request(cardQuery({ deck_id: deckId }, due)),
  examCards: (examId, due = false) => request(cardQuery({ exam_id: examId }, due)),
  createCard: (body) => request('/cards', json('POST', body)),
  updateCard: (id, body) => request(`/cards/${id}`, json('PATCH', body)),
  deleteCard: (id) => request(`/cards/${id}`, { method: 'DELETE' }),
  repositionCard: (id, position) => request(`/cards/${id}/position`, json('PUT', { position })),
  reviewCard: (id, rating) => request(`/cards/${id}/review`, json('POST', { rating })),

  dueCount: () => request('/statistics/due'),
  examStats: (id) => request(`/statistics/exams/${id}`),
  deckStats: (id) => request(`/statistics/decks/${id}`),
  examHistory: (id) => request(`/statistics/exams/${id}/consolidated-history`),

  uploadImage: (file) => {
    const body = new FormData()
    body.append('file', file)
    return request('/uploads/images', { method: 'POST', body })
  },

  exportExam: (id) => request(`/transfer/exams/${id}`),
  exportDeck: (id) => request(`/transfer/decks/${id}`),
  importExam: (body) => request('/transfer/exams', json('POST', body)),
  importDeck: (body, examId) => request(`/transfer/decks${examId ? `?exam_id=${examId}` : ''}`, json('POST', body)),
}

export const gradesApi = {
  years: () => gradesRequest('/years'),
  createYear: (body) => gradesRequest('/years', json('POST', body)),
  updateYear: (id, body) => gradesRequest(`/years/${id}`, json('PATCH', body)),
  repositionYear: (id, position) => gradesRequest(`/years/${id}/position`, json('PUT', { position })),
  deleteYear: (id) => gradesRequest(`/years/${id}`, { method: 'DELETE' }),

  modules: () => gradesRequest('/modules'),
  createModule: (body) => gradesRequest('/modules', json('POST', body)),
  updateModule: (id, body) => gradesRequest(`/modules/${id}`, json('PATCH', body)),
  deleteModule: (id) => gradesRequest(`/modules/${id}`, { method: 'DELETE' }),

  submodules: () => gradesRequest('/submodules'),
  createSubmodule: (body) => gradesRequest('/submodules', json('POST', body)),
  updateSubmodule: (id, body) => gradesRequest(`/submodules/${id}`, json('PATCH', body)),
  deleteSubmodule: (id) => gradesRequest(`/submodules/${id}`, { method: 'DELETE' }),

  overall: () => gradesRequest('/statistics/overall'),
  progression: () => gradesRequest('/statistics/progression'),
  maxPoints: () => gradesRequest('/grading/max-points'),
}

export async function loadGradesOverview() {
  const [overall, progression] = await Promise.all([gradesApi.overall(), gradesApi.progression()])
  return { overall, progression }
}

export async function loadGradesTree() {
  const [years, modules, submodules, progression, overall, maxPoints] = await Promise.all([
    gradesApi.years(),
    gradesApi.modules(),
    gradesApi.submodules(),
    gradesApi.progression(),
    gradesApi.overall(),
    gradesApi.maxPoints(),
  ])
  const yearStats = new Map(progression.map((p) => [p.year_id, p]))
  const tree = years.map((year) => ({
    ...year,
    grade: yearStats.get(year.id)?.grade ?? null,
    ects: yearStats.get(year.id)?.ects ?? 0,
    modules: modules
      .filter((m) => m.year_id === year.id)
      .map((module) => ({ ...module, submodules: submodules.filter((s) => s.module_id === module.id) })),
  }))
  return { tree, overall, maxPoints }
}

const withStats = (decks) =>
  Promise.all(decks.map(async (deck) => ({ ...deck, stats: await api.deckStats(deck.id) })))

export async function loadExamDecks(examId) {
  return withStats(await api.examDecks(examId))
}

export async function loadLooseDecks() {
  return withStats(await api.looseDecks())
}

export async function loadExamsOverview() {
  const exams = await api.exams()
  return Promise.all(
    exams.map(async (exam) => {
      const [stats, decks] = await Promise.all([api.examStats(exam.id), api.examDecks(exam.id)])
      return { ...exam, stats, deckCount: decks.length }
    }),
  )
}

export const imageUrl = (name) => (name ? `${BASE}/uploads/images/${name}` : null)

export function downloadJson(data, name) {
  const safe = (name || 'export').replace(/[^\p{L}\p{N}\-_ ]+/gu, '').trim() || 'export'
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${safe}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export function useLoad(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const load = useCallback(loader, deps)

  const run = useCallback(
    (isCurrent = () => true) =>
      load().then(
        (data) => isCurrent() && setState({ data, error: null, loading: false }),
        (error) => isCurrent() && setState({ data: null, error, loading: false }),
      ),
    [load],
  )

  useEffect(() => {
    let current = true
    setState((s) => ({ ...s, loading: true }))
    run(() => current)
    return () => {
      current = false
    }
  }, [run])

  return { ...state, reload: run }
}
