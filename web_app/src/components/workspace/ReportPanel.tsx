import { useState } from 'react'
import { FileText, Download, Loader2, CheckCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useGenerateReport, useDownloadReport } from '@/hooks/useReport'
import ReactMarkdown from 'react-markdown'
import { toast } from 'sonner'

interface ReportPanelProps {
  sessionId: string
}

export function ReportPanel({ sessionId }: ReportPanelProps) {
  const [reportContent, setReportContent] = useState<string | null>(null)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState<string | null>(null)

  const generateMutation = useGenerateReport(sessionId)
  const { downloadFile } = useDownloadReport(sessionId)

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      // 1. Generate Markdown for preview
      setGenerationStep('Generating report...')
      const result = await generateMutation.mutateAsync('markdown')
      setGeneratedAt(result.generated_at)
      
      // Fetch the markdown content for preview
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${API_URL}/sessions/${sessionId}/report/download`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (response.ok) {
        const text = await response.text()
        setReportContent(text)
      }
      
      // 2. Generate Checklist
      setGenerationStep('Populating checklist...')
      await generateMutation.mutateAsync('checklist')
      
      // 3. Generate DOCX
      setGenerationStep('Preparing DOCX...')
      await generateMutation.mutateAsync('docx')
      
      toast.success('Report and checklist generated successfully')
    } catch (error) {
      toast.error('Failed to generate one or more report formats')
      console.error(error)
    } finally {
      setIsGenerating(false)
      setGenerationStep(null)
    }
  }

  const handleDownload = async (type: 'report' | 'checklist' | 'checklist-docx') => {
    try {
      await downloadFile(type)
      toast.success('Download started')
    } catch (error) {
      toast.error('Failed to download file')
      console.error(error)
    }
  }

  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          <h2 className="font-semibold">Review Report</h2>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={isGenerating}
          size="sm"
        >
          {isGenerating ? (
            <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> {generationStep || 'Generating...'}</>
          ) : generatedAt ? (
            <><RefreshCw className="h-4 w-4 mr-2" /> Regenerate</>
          ) : (
            'Generate Report'
          )}
        </Button>
      </div>

      {/* Status */}
      {generatedAt && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <CheckCircle className="h-3.5 w-3.5 text-green-500" />
          Generated {new Date(generatedAt).toLocaleString()}
        </div>
      )}

      {/* Preview */}
      {reportContent ? (
        <div className="flex-1 overflow-auto border rounded-lg p-4 bg-muted/30">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{reportContent}</ReactMarkdown>
          </div>
        </div>
      ) : (
        !isGenerating && (
          <div className="flex-1 flex items-center justify-center text-muted-foreground border rounded-lg bg-muted/10 border-dashed">
            <div className="text-center p-6">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">Generate a report to see the preview</p>
              <p className="text-sm mt-1">Includes evidence citations and validation results</p>
            </div>
          </div>
        )
      )}
      
      {/* Loading State Skeleton */}
      {isGenerating && !reportContent && (
         <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground border rounded-lg bg-muted/10">
           <Loader2 className="h-8 w-8 animate-spin mb-4 opacity-50" />
           <p>{generationStep || 'Generating analysis...'}</p>
         </div>
      )}

      {/* Download Buttons */}
      {generatedAt && (
        <div className="flex gap-2 pt-4 border-t overflow-x-auto">
          <Button variant="outline" size="sm" onClick={() => handleDownload('report')}>
            <Download className="h-4 w-4 mr-2" /> Markdown
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleDownload('checklist')}>
            <Download className="h-4 w-4 mr-2" /> Checklist
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleDownload('checklist-docx')}>
            <Download className="h-4 w-4 mr-2" /> DOCX
          </Button>
        </div>
      )}
    </div>
  )
}
