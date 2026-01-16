import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  FileText,
  Download,
  Loader2,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import ReactMarkdown from 'react-markdown'
import { useGenerateReport, useDownloadReport, useExistingReport } from '@/hooks/useReport'
import { FinalDeterminationPanel } from './FinalDeterminationPanel'

interface ReportPanelProps {
  sessionId?: string
}

export function ReportPanel({ sessionId: propSessionId }: ReportPanelProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const sessionId = propSessionId ?? paramSessionId ?? ''

  const [reportContent, setReportContent] = useState<string | null>(null)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)
  const [summary, setSummary] = useState<{
    requirements_total: number
    requirements_covered: number
    requirements_partial: number
    requirements_missing: number
    overall_coverage: number
  } | null>(null)

  const generateMutation = useGenerateReport(sessionId)
  const { downloadFile } = useDownloadReport(sessionId)
  const { data: existingReport, isLoading: isLoadingExisting } = useExistingReport(sessionId)

  // Load existing report content on mount
  useEffect(() => {
    if (existingReport && !reportContent) {
      setReportContent(existingReport.content)
      setGeneratedAt(existingReport.generated_at)
      if (existingReport.summary) {
        setSummary(existingReport.summary)
      }
    }
  }, [existingReport, reportContent])

  const handleGenerate = async () => {
    toast.info('Generating report...', { description: 'This may take a moment.' })
    try {
      // Generate all formats: markdown report, checklist, and docx
      const result = await generateMutation.mutateAsync('markdown')
      setGeneratedAt(result.generated_at)
      setSummary(result.summary)

      // Generate checklist and docx formats in parallel (for download buttons)
      await Promise.all([
        generateMutation.mutateAsync('checklist').catch(() => {}),
        generateMutation.mutateAsync('docx').catch(() => {}),
      ])

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`${API_URL}/sessions/${sessionId}/report/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        const text = await response.text()
        setReportContent(text)
        toast.success('Report generated', { description: 'Preview and download options available.' })
      } else {
        toast.error('Failed to fetch report content')
      }
    } catch (error) {
      toast.error('Report generation failed', {
        description: error instanceof Error ? error.message : 'Please try again.',
      })
    }
  }

  const handleDownload = async (type: 'report' | 'checklist' | 'checklist-docx') => {
    try {
      await downloadFile(type)
      const names = {
        report: 'Markdown report',
        checklist: 'Checklist markdown',
        'checklist-docx': 'DOCX checklist',
      }
      toast.success(`Downloaded ${names[type]}`)
    } catch (error) {
      toast.error('Download failed', {
        description: error instanceof Error ? error.message : 'Please try again.',
      })
    }
  }

  if (!sessionId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4 text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-sm font-medium">No session selected</p>
      </div>
    )
  }

  if ((generateMutation.isPending || isLoadingExisting) && !reportContent) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 p-4 space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      {/* Final Determination Section */}
      <FinalDeterminationPanel sessionId={sessionId} />

      {/* Report Generation Section */}
      {!reportContent && !generateMutation.isPending ? (
        <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
          <FileText className="h-12 w-12 mb-4 opacity-30" />
          <p className="text-sm font-medium">No Report Generated</p>
          <p className="text-xs text-center mt-2 max-w-[280px]">
            Generate a review report with evidence citations, validation results,
            and coverage summary for download.
          </p>
          <Button className="mt-4" onClick={handleGenerate}>
            <FileText className="h-4 w-4 mr-2" />
            Generate Report
          </Button>
        </div>
      ) : (
        <div className="flex flex-col">
          <div className="px-4 py-3 border-t bg-muted/20">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <span className="text-sm font-medium">Review Report</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                    Regenerate
                  </>
                )}
              </Button>
            </div>

            {generatedAt && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                Generated {new Date(generatedAt).toLocaleString()}
              </div>
            )}

            {summary && (
              <div className="flex items-center gap-4 text-xs">
                <span className="text-green-600">
                  {summary.requirements_covered} covered
                </span>
                <span className="text-yellow-600">
                  {summary.requirements_partial} partial
                </span>
                <span className="text-red-600">
                  {summary.requirements_missing} missing
                </span>
                <span className="text-muted-foreground">
                  ({summary.overall_coverage}% coverage)
                </span>
              </div>
            )}
          </div>

          <div className="p-4">
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{reportContent}</ReactMarkdown>
            </div>
          </div>

          <div className="px-4 py-3 border-t bg-muted/20">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload('report')}
              >
                <Download className="h-3.5 w-3.5 mr-1.5" />
                Report (.md)
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload('checklist')}
              >
                <Download className="h-3.5 w-3.5 mr-1.5" />
                Checklist (.md)
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload('checklist-docx')}
              >
                <Download className="h-3.5 w-3.5 mr-1.5" />
                Checklist (.docx)
              </Button>
            </div>
          </div>
        </div>
      )}
    </ScrollArea>
  )
}
