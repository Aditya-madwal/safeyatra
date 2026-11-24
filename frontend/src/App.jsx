import { Navigate, Route, Routes } from 'react-router-dom'
import Header from './components/Header.jsx'
import { ToastProvider } from './components/ui.jsx'
import AdminPage from './pages/AdminPage.jsx'
import MapPage from './pages/MapPage.jsx'
import ReportPage from './pages/ReportPage.jsx'

export default function App() {
  return (
    <ToastProvider>
      <div className="flex h-full flex-col overflow-hidden bg-base-200 text-base-content">
        <Header />
        <main className="relative min-h-0 flex-1">
          <Routes>
            <Route path="/" element={<MapPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </ToastProvider>
  )
}
