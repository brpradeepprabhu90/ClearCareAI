import { Loader2 } from 'lucide-react'

export default function ProcessingView() {
  return (
    <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
      <Loader2 className="w-16 h-16 text-primary animate-spin mb-6" />
      <h2 className="text-3xl font-semibold mb-3">Processing Document</h2>
      <p className="text-lg text-gray-500">Extracting clinical data using AI agents...</p>
    </div>
  )
}
