import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import ExamPage from './pages/ExamPage.jsx'
import DeckPage from './pages/DeckPage.jsx'
import StudyPage from './pages/StudyPage.jsx'
import { NotFound } from './components/Stats.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/exams/:examId" element={<ExamPage />} />
        <Route path="/decks/:deckId" element={<DeckPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="/study/:scope/:id?" element={<StudyPage />} />
    </Routes>
  )
}
