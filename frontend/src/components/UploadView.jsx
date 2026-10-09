import { useRef, useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { FileUp, FileText, Brain, Sparkles } from 'lucide-react'

export default function UploadView() {
  const fileInput = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const { setView, setExtractedData, setError } = useAppStore()

  const handleFile = async (file) => {
    if (!file) return
    setView('processing')
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Extraction failed')
      }
      const data = await res.json()
      setExtractedData(data.extractor)
      setView('confirm')
    } catch (e) {
      setError(e.message)
      setView('upload')
      alert(e.message)
    }
  }

  return (
    <div className="flex flex-col items-center text-center max-w-3xl mx-auto animate-fade-in">
      <h2 className="text-4xl font-bold mb-4">
        Transform confusing discharge papers into <span className="gradient-text">clear, actionable plans.</span>
      </h2>
      <p className="text-lg text-gray-500 mb-12">
        Get a clear, easy-to-read daily schedule and safety check from your complex hospital paperwork in seconds.
      </p>

      <div 
        className={`w-full max-w-xl p-12 border-2 border-dashed rounded-3xl bg-white transition-all cursor-pointer
          ${isDragging ? 'border-primary bg-blue-50 scale-105' : 'border-gray-300 hover:border-primary'}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          handleFile(e.dataTransfer.files[0])
        }}
        onClick={() => fileInput.current?.click()}
      >
        <FileUp className="w-16 h-16 mx-auto text-primary mb-4" />
        <h3 className="text-xl font-semibold mb-2">Upload Discharge Papers</h3>
        <p className="text-gray-500 mb-6">Drag & drop PDF, JPG, or PNG</p>
        <input 
          type="file" 
          ref={fileInput}
          className="hidden" 
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <button 
          className="btn-primary"
          onClick={(e) => { e.stopPropagation(); fileInput.current?.click() }}
        >
          Select File
        </button>
      </div>

      <div className="flex items-center justify-center gap-8 mt-16 text-gray-600 font-medium">
        <div className="flex items-center gap-2"><FileText className="text-primary"/> 1. Upload PDF</div>
        <div className="text-gray-300">→</div>
        <div className="flex items-center gap-2"><Brain className="text-primary"/> 2. AI Analyzes</div>
        <div className="text-gray-300">→</div>
        <div className="flex items-center gap-2"><Sparkles className="text-primary"/> 3. Get Care Plan</div>
      </div>
    </div>
  )
}
