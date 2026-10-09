import { useAppStore } from '../store/useAppStore'
import { ShieldAlert, BookOpen, Utensils, Clock, AlertTriangle, Printer, RotateCcw } from 'lucide-react'

export default function DashboardView() {
  const { dashboardData, language, setLanguage, resetApp } = useAppStore()
  
  if (!dashboardData) return null

  const { safety, explainer, scheduler } = dashboardData
  const l = language

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold">Patient Care Plan</h2>
        <div className="flex bg-gray-100 p-1 rounded-lg">
          <button 
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${language === 'en' ? 'bg-white shadow-sm text-primary' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setLanguage('en')}
          >
            English
          </button>
          <button 
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${language === 'es' ? 'bg-white shadow-sm text-primary' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setLanguage('es')}
          >
            Español
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Safety Check (Hero) */}
        <div className="bento-card md:col-span-3 border-l-4 border-l-danger">
          <div className="flex items-center gap-3 mb-6">
            <ShieldAlert className="w-8 h-8 text-danger" />
            <h3 className="text-2xl font-bold text-danger">Safety Check</h3>
            <span className="ml-auto text-xs font-semibold text-green-700 bg-green-100 px-3 py-1 rounded-full">
              ✓ Checked against Guidelines
            </span>
          </div>
          
          <div className="space-y-4">
            {safety.flags.length === 0 ? (
              <p className="text-gray-600 font-medium">No critical drug interactions found.</p>
            ) : (
              safety.flags.map((flag, i) => (
                <div key={i} className="bg-red-50 p-4 rounded-xl border border-red-100">
                  <h4 className="font-bold text-red-800 text-lg mb-1">{flag[`headline_${l}`]}</h4>
                  <div className="text-red-600 font-semibold mb-2">{flag[`action_${l}`]}</div>
                  <p className="text-sm text-gray-700 mb-2">{flag[`detail_${l}`]}</p>
                  <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">Source: {flag.citation}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="bento-card md:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="w-6 h-6 text-primary" />
            <h3 className="text-xl font-bold">Summary</h3>
          </div>
          <ul className="space-y-3">
            {explainer[`summary_${l}`]?.map((item, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-primary mt-1">•</span>
                <span className="text-gray-700">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Diet & Activity */}
        <div className="bento-card">
          <div className="flex items-center gap-3 mb-4">
            <Utensils className="w-6 h-6 text-orange-500" />
            <h3 className="text-xl font-bold">Diet & Activity</h3>
          </div>
          <ul className="space-y-3">
            {explainer[`diet_activity_${l}`]?.map((item, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-orange-500 mt-1">•</span>
                <span className="text-gray-700">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Schedule */}
        <div className="bento-card md:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <Clock className="w-6 h-6 text-blue-500" />
            <h3 className="text-xl font-bold">Daily Schedule</h3>
          </div>
          <div className="relative border-l-2 border-gray-100 ml-3 space-y-6">
            {scheduler[`timeline_${l}`]?.map((item, i) => (
              <div key={i} className="pl-6 relative">
                <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white"></div>
                <div className="font-bold text-gray-900 mb-1">{item.time}</div>
                <div className="text-gray-600 bg-gray-50 p-3 rounded-lg">{item.action}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Warnings */}
        <div className="bento-card bg-yellow-50 border-yellow-200">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-yellow-600" />
            <h3 className="text-xl font-bold text-yellow-800">When to call the doctor</h3>
          </div>
          
          <h4 className="text-sm font-semibold text-yellow-700 mb-2 uppercase tracking-wide">From your papers</h4>
          <ul className="space-y-2 mb-6">
            {scheduler[`doc_warnings_${l}`]?.map((item, i) => (
              <li key={i} className="text-yellow-900 text-sm flex gap-2"><span className="text-yellow-600">•</span> {item}</li>
            ))}
          </ul>
          
          <h4 className="text-sm font-semibold text-yellow-700 mb-2 uppercase tracking-wide">General Safety</h4>
          <ul className="space-y-2">
            {scheduler[`general_warnings_${l}`]?.map((item, i) => (
              <li key={i} className="text-yellow-900 text-sm flex gap-2"><span className="text-yellow-600">•</span> {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="flex justify-between items-center mt-8 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-500 flex items-center gap-2">
          <ShieldAlert size={16} /> Not medical advice. Confirm with your care team.
        </p>
        <div className="flex gap-4">
          <button className="btn-secondary flex items-center gap-2" onClick={resetApp}>
            <RotateCcw size={18} /> Start Over
          </button>
          <button className="btn-primary flex items-center gap-2" onClick={() => window.print()}>
            <Printer size={18} /> Print Plan
          </button>
        </div>
      </div>
    </div>
  )
}
