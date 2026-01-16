import { useMutation, useQuery } from '@tanstack/react-query'
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

interface ExistingReportResult {
  content: string
  generated_at: string
  summary?: ReportResult['summary']
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

/**
 * Hook to check if a report already exists and fetch its content.
 * Used to display existing reports when navigating to the Report tab.
 */
export function useExistingReport(sessionId: string) {
  return useQuery({
    queryKey: ['existing-report', sessionId],
    queryFn: async (): Promise<ExistingReportResult | null> => {
      if (!sessionId) return null

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'
      const token = localStorage.getItem('auth_token')

      // Try to download existing report
      const response = await fetch(`${API_URL}/sessions/${sessionId}/report/download`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) {
        // Report doesn't exist yet
        return null
      }

      const content = await response.text()

      // Try to extract generated_at from the report metadata
      // The report typically has a header with generation timestamp
      const timestampMatch = content.match(/Generated:\s*(.+?)(?:\n|$)/i)
      const generated_at = timestampMatch?.[1] || new Date().toISOString()

      return {
        content,
        generated_at,
      }
    },
    enabled: !!sessionId,
    staleTime: 30000, // Consider stale after 30 seconds
    retry: false, // Don't retry if report doesn't exist
  })
}
