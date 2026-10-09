import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { Loader2 } from 'lucide-react'

export default function ConfirmView() {
  const { extractedData, setDashboardData, setView, setError } = useAppStore()
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/generate_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extractedData)
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Generation failed')
      }
      const data = await res.json()
      setDashboardData({
        safety: data.safety_check,
        explainer: data.explainer,
        scheduler: data.scheduler
      })
      setView('dashboard')
    } catch (e) {
      setError(e.message)
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto bento-card animate-fade-in">
      <h2 className="text-2xl font-bold mb-2">Confirm Extracted Medications</h2>
      <p className="text-gray-500 mb-6">Please verify the medications extracted from the document before proceeding.</p>
      
      <div className="space-y-4 mb-8">
        {extractedData?.medications?.map((med, i) => (
          <div key={i} className="flex justify-between items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
            <div>
              <div className="font-semibold text-lg">{med.name} <span className="text-gray-500 font-normal text-sm">{med.dose}</span></div>
              <div className="text-primary font-medium">{med.frequency}</div>
            </div>
            <div className="text-sm text-gray-400 bg-white px-3 py-1 rounded-full border border-gray-200">
              {med.source}
            </div>
          </div>
        ))}
        {(!extractedData?.medications || extractedData.medications.length === 0) && (
          <div className="text-gray-500 p-4 text-center">No medications found.</div>
        )}
      </div>

      <button 
        className="btn-primary w-full flex justify-center items-center gap-2"
        onClick={handleConfirm}
        disabled={loading}
      >
        {loading && <Loader2 className="w-5 h-5 animate-spin" />}
        {loading ? 'Generating Plan...' : 'Confirm & Generate Plan'}
      </button>
    </div>
  )
}
