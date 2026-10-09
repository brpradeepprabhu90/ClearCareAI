import { useAppStore } from './store/useAppStore'
import UploadView from './components/UploadView'
import ProcessingView from './components/ProcessingView'
import ConfirmView from './components/ConfirmView'
import DashboardView from './components/DashboardView'
import { ShieldCheck } from 'lucide-react'

function App() {
  const view = useAppStore((state) => state.view)

  return (
    <div className="min-h-screen bg-background">
      <header className="flex justify-between items-center p-6 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <img src="/logo.jpg" alt="ClearCare AI Logo" className="w-10 h-10 rounded-xl object-cover shadow-sm" />
          <h1 className="text-2xl font-bold">ClearCare AI</h1>
        </div>
        <nav className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1.5 rounded-full">
            <ShieldCheck size={16} />
            <span>Processed in memory. Nothing is stored.</span>
          </div>
        </nav>
      </header>

      <main className="max-w-6xl mx-auto p-6 mt-8">
        {view === 'upload' && <UploadView />}
        {view === 'processing' && <ProcessingView />}
        {view === 'confirm' && <ConfirmView />}
        {view === 'dashboard' && <DashboardView />}
      </main>
    </div>
  )
}

export default App
