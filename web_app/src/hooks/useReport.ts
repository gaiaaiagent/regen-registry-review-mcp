import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

interface ReportResult {
  session_id: string
  format: string
  report_path: string
  generated_at: string
  summary: {
    requirements_total: number
    requirements_covered: number
    requirements_partial: number
    requirements_missing: number
    overall_coverage: number
  }
  download_url: string
}

export function useGenerateReport(sessionId: string) {
  return useMutation({
    mutationFn: async (format: 'markdown' | 'checklist' | 'docx') => {
      const { data, error } = await api.POST('/sessions/{session_id}/report', {
        params: {
          path: { session_id: sessionId },
          query: { format }
        }
      })
      if (error) throw new Error('Failed to generate report')
      return data as ReportResult
    }
  })
}

export function useDownloadReport(sessionId: string) {
  const downloadFile = async (endpoint: 'report' | 'checklist' | 'checklist-docx') => {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'
    const token = localStorage.getItem('auth_token')

    const urls = {
      'report': `${API_URL}/sessions/${sessionId}/report/download`,
      'checklist': `${API_URL}/sessions/${sessionId}/checklist/download`,
      'checklist-docx': `${API_URL}/sessions/${sessionId}/checklist/download-docx`
    }

    const response = await fetch(urls[endpoint], {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (!response.ok) {
      throw new Error('Failed to download file')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = endpoint === 'checklist-docx' ? 'checklist.docx' : 'report.md'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  return { downloadFile }
}
