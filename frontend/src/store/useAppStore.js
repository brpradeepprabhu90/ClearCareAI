import { create } from 'zustand'

export const useAppStore = create((set) => ({
  view: 'upload', // upload, processing, confirm, dashboard
  language: 'en',
  extractedData: null,
  dashboardData: null,
  error: null,
  
  setView: (view) => set({ view }),
  setLanguage: (language) => set({ language }),
  setExtractedData: (data) => set({ extractedData: data }),
  setDashboardData: (data) => set({ dashboardData: data }),
  setError: (error) => set({ error }),
  
  resetApp: () => set({ 
    view: 'upload', 
    extractedData: null, 
    dashboardData: null, 
    error: null 
  })
}))
